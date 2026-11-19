---
schema: 2
id: reading-16-measure-between-two-selections
title: Measure the distance between two selected entities with IMeasure
answers: "How do I measure the distance between two things I have selected (an axis and a plane, say) from code, the way the Measure tool does?"
keywords: [IMeasure, CreateMeasure, Calculate, measure tool from code, distance between axis and plane, NormalDistance, DISPATCH_METHOD, Invoke, property get, bool object is not callable, late binding, measure in an assembly]
api: [IModelDocExtension.CreateMeasure, IMeasure.Calculate, IMeasure.Distance, IMeasure.NormalDistance, IModelDocExtension.SelectByID2]
language: [python]
status: verified
verified_on: SolidWorks 2026 (revision 34.1.1) and SolidWorks 2024 SP5 (32.5.0)
majors: [32, 34]
evidence: []
recipe_status: null
recipe_evidence: []
superseded_by: null
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

The Gear-Generator probe's calls (`assembly_rebuild_scope`, tier 7), as copied
from [`code/python/gear_train/gear_train_check.py`](../../code/python/gear_train/gear_train_check.py). It ran on SolidWorks 2026 (34.1.1) and 2024 SP5 (32.5.0), each started fresh by the runner (results `gear-train-check-20261114-140356` and `gear-train-check-20261114-140631` beside it).

```python
import pythoncom
from win32com.client import VARIANT


def call(obj, name, *args):
    """Late-bound member: invoked when given arguments, read by attribute access otherwise."""
    member = getattr(obj, name)
    return member(*args) if args else member


def null():
    return VARIANT(pythoncom.VT_DISPATCH, None)              # a typed Nothing


def selected_count(doc):
    return int(call(call(doc, "SelectionManager"), "GetSelectedObjectCount2", -1) or 0)


def top_features(doc):
    out, feature = [], call(doc, "FirstFeature")
    while feature is not None:
        out.append(feature)
        feature = call(feature, "GetNextFeature")
    return out


def planes(doc):
    """The reference planes in tree order: Front, Top, Right in an English template."""
    return [f for f in top_features(doc) if call(f, "GetTypeName2") == "RefPlane"]


def select_feature(doc, feature, append=False, mark=0):
    """IFeature.Select2, judged by the selection count and retried briefly; then SelectByID2 by name."""
    if not append:
        call(doc, "ClearSelection2", True)
    before = selected_count(doc)
    for _ in range(4):
        if call(feature, "Select2", append, mark) and selected_count(doc) > before:
            return True
        time.sleep(0.25)
    kind = {"RefPlane": "PLANE", "RefAxis": "AXIS", "ProfileFeature": "SKETCH"}.get(
        call(feature, "GetTypeName2"), "BODYFEATURE")
    return bool(call(call(doc, "Extension"), "SelectByID2", str(call(feature, "Name")), kind, 0.0, 0.0, 0.0,
                     append, mark, null(), 0)) and selected_count(doc) > before


def _invoke_method(obj, name, *args):
    """Invoke a COM member as a method, where late binding would reach it as a property get."""
    oleobj = obj._oleobj_
    return oleobj.Invoke(oleobj.GetIDsOfNames(name), 0, pythoncom.DISPATCH_METHOD, True, *args)


def axis_to_right_plane_m(asm, axis_ref):
    """IMeasure between a component's axis ("<axis>@<component>@<assembly>") and the assembly's Right plane."""
    ext = call(asm, "Extension")
    call(asm, "ClearSelection2", True)
    try:
        if not (call(ext, "SelectByID2", axis_ref, "AXIS", 0.0, 0.0, 0.0, False, 0, null(), 0)
                and selected_count(asm) == 1):
            return None
        if not select_feature(asm, planes(asm)[2], append=True) or selected_count(asm) != 2:
            return None
        measure = call(ext, "CreateMeasure")
        if measure is None or not _invoke_method(measure, "Calculate", null()):
            return None
        return float(call(measure, "Distance")), float(call(measure, "NormalDistance"))   # metres
    finally:
        call(asm, "ClearSelection2", True)
```

- `CreateMeasure` on **IModelDocExtension**, reached by attribute access through
  `call` (it takes no arguments), returned the `IMeasure`.
- `Calculate(null)` on **IMeasure**, invoked by its dispid with
  `pythoncom.DISPATCH_METHOD` and a typed null dispatch (`null()`, VBA's
  `Nothing`: measure the current selection), returned `True`. The second form,
  with `None` in place of the typed null, was never needed (the probe tried it
  only if the first returned nothing).
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

That failing form is recorded in a comment in the probe's source, from a 2026
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
