---
id: reading-16-measure-between-two-selections
title: Measure the distance between two selected entities with IMeasure
status: verified
verified_on: SolidWorks 2026 (revision 34.1.1) and SolidWorks 2024 SP5 (32.5.0)
language: [python]
api: [IModelDocExtension.CreateMeasure, IMeasure.Calculate, IMeasure.Distance, IMeasure.NormalDistance, IModelDocExtension.SelectByID2]
keywords: [IMeasure, CreateMeasure, Calculate, measure tool from code, distance between axis and plane, NormalDistance, DISPATCH_METHOD, Invoke, property get, bool object is not callable, late binding, measure in an assembly]
answers: "How do I measure the distance between two things I have selected (an axis and a plane, say) from code, the way the Measure tool does?"
---

# Measure the distance between two selected entities with IMeasure

## What this is for

Checking where something ended up, in the assembly's own coordinates, without
working the geometry out yourself: how far a component's axis is from a plane
after a skeleton part's global changed, say. The Measure tool's API is an
`IMeasure` made by the document's extension; it measures whatever is selected.
Through pywin32 late binding, its `Calculate` has to be invoked explicitly as a
method.

## The call

From the Gear-Generator probe (`assembly_rebuild_scope`, tier 7):

```python
def _invoke_method(obj: Any, name: str, *args: Any) -> Any:
    """Invoke a COM member as a method, where late binding would reach it as a property get (p4_nonparallel's way)."""
    import pythoncom  # noqa: PLC0415 - Windows only, and only ever on the worker

    oleobj = obj._oleobj_  # noqa: SLF001
    return oleobj.Invoke(oleobj.GetIDsOfNames(name), 0, pythoncom.DISPATCH_METHOD, True, *args)


def _axis_from_right(px: Px, asm: Any, axis_ref: str) -> Dict[str, Any]:
    """``IModelDocExtension.CreateMeasure`` between a layout axis in the assembly and the assembly's Right plane.

    The axis is selected by ``SelectByID2 "<axis>@<component>@<assembly>"``
    (probe layout_part_without_body), the plane by tree order (the third plane).
    """
    out: Dict[str, Any] = {"axis": axis_ref}
    ext = sc.extension(asm)
    call(asm, "ClearSelection2", True)
    try:
        out["axis_selected"] = bool(call(ext, "SelectByID2", axis_ref, "AXIS", 0.0, 0.0, 0.0, False, 0, sc.null(), 0)
                                    and sc.selected_count(asm) == 1)
        out["plane_selected"] = bool(out["axis_selected"] and sc.select_plane(asm, 3, append=True)
                                     and sc.selected_count(asm) == 2)
        if not out["plane_selected"]:
            return out
        got, measure = px.attempt("CreateMeasure", lambda: call(ext, "CreateMeasure"))
        if not got or measure is None:
            out["measure"] = None
            return out
        # The first run (2026, 34.1.1) found late binding reaching Calculate as a property get: it answered a bool
        # and "'bool' object is not callable" for the argument, as CreateTransform did (make_transform). So it is
        # invoked as the method it is, with VBA's Nothing first, then an empty argument.
        for label, argument in (("Calculate(null dispatch), invoked as a method", sc.null()),
                                ("Calculate(None), invoked as a method", None)):
            ok, value = px.attempt(f"IMeasure.{label}", lambda a=argument: _invoke_method(measure, "Calculate", a))
            if ok and value:
                out["calculate"] = label
                break
        if "calculate" not in out:
            return out
        for name in ("Distance", "NormalDistance"):
            ok, value = px.attempt(f"IMeasure.{name}", lambda n=name: call(measure, n))
            out[f"{name}_mm"] = round(float(value) * sc.MM, 9) if ok and isinstance(value, (int, float)) else None
    finally:
        call(asm, "ClearSelection2", True)
    return out
```

- `CreateMeasure` on **IModelDocExtension**, reached by attribute access through
  `call` (it takes no arguments), returned the `IMeasure`.
- `Calculate(null)` on **IMeasure**, invoked by its dispid with
  `pythoncom.DISPATCH_METHOD` and a typed null dispatch (`sc.null()`, VBA's
  `Nothing`: measure the current selection), returned `True`. The second form,
  with `None`, was never needed.
- `Distance` and `NormalDistance` on **IMeasure**, property gets, in **metres**.
- The two entities: a component's reference axis selected by
  `SelectByID2("<axis>@<component>@<assembly>", "AXIS", 0, 0, 0, False, 0, null, 0)`
  and the assembly's third plane (Right) appended, checked by the selection
  count ([assemblies/02](../assemblies/02-mates-from-code.md)).

## Why it is not obvious

`Calculate` takes one argument, but through pywin32's dynamic dispatch the
attribute is fetched as a **property get**: SolidWorks runs it there and then
with no argument and hands back a `bool`, so `measure.Calculate(None)` fails
with `'bool' object is not callable`. That is [GOTCHAS §55](../../GOTCHAS.md)'s
`AddBodies` case again, and the cure is the one `CreateTransform` needed
([assemblies/04](../assemblies/04-mates-between-non-parallel-axes.md#why-createtransform-needs-invoke)):
invoke the dispid as a method.

That failing form is recorded in the probe's source comment above, from a 2026
(34.1.1) run whose results were not kept; no kept result file shows it. Every
kept run used the `Invoke` form, and it worked in all of them.

## What it does not do

- Only an axis-to-plane distance between parallel entities was measured, where
  `Distance` and `NormalDistance` agree. Other pairs, angles, and the other
  `IMeasure` members were not read.
- Whether the measure must be recalculated after the model changes, or can be
  reused, was not tested: the probe made a fresh `IMeasure` for each reading.
- The `Calculate(None)` form was never reached.

## Evidence

SolidWorks 2026 (revision 34.1.1), full runs 20261114-013909, 20261114-030832
and 20261114-034458, and SolidWorks 2024 SP5 (32.5.0), run 20261114-014813;
Python over pywin32 late binding. In each, for four assemblies and several
readings each:

- `attempt:CreateMeasure = {'ok': True, 'value': 'CDispatch'}`;
- `IMeasure.Calculate(null dispatch), invoked as a method: returned True`;
- after a skeleton part's global moved a shaft axis 5 mm further from the
  Right plane, `IMeasure.Distance` and `IMeasure.NormalDistance` both read the
  new distance the global asked for, in metres, to every digit printed, on both
  versions.

The result files are kept in the Gear-Generator repository, not here.

## See also

- [assemblies/12 — Rebuild an assembly without marking every part modified](../assemblies/12-rebuild-scope-and-the-save-flag.md) — where these measurements were the check
- [assemblies/04 — Mates between non-parallel axes](../assemblies/04-mates-between-non-parallel-axes.md) — `Invoke` with `DISPATCH_METHOD` for `CreateTransform`
- [connect/02 — Attach from Python](../connect/02-attach-from-python.md) — attribute access versus a call
- [reading/13 — Measure a wall between two bodies](13-measure-a-wall-between-two-bodies.md) — measuring from faces instead
- [reading/15 — Measure a part that has no dimensions](15-measure-a-part-that-has-no-dimensions.md)
- [GOTCHAS §55](../../GOTCHAS.md)
