---
id: assemblies-10-mate-a-gear-train-that-turns
title: Mate gears on their shafts into a train that turns, with gear mates and lock mates
status: verified
verified_on: SolidWorks 2026 (revisions 34.0.0 and 34.1.1) and SolidWorks 2024 SP5 (32.5.0)
language: [python]
api: [IAssemblyDoc.AddMate5, IAssemblyDoc.UnfixComponent, IComponent2.Select4, ISelectionMgr.CreateSelectData, IComponent2.GetCorresponding, IComponent2.GetConstrainedStatus, IFeature.GetDefinition, IGearMateFeatureData.GearRatioNumerator, IGearMateFeatureData.GearRatioDenominator, IGearMateFeatureData.Reverse, IMate2.Alignment, IMate2.MateEntity, IMateEntity2.ReferenceComponent]
keywords: [gear train, gear mate, swMateGEAR, AddMate5 gear, gear ratio order, numerator first selection, Flip, mesh direction, ring gear, internal gear, lock mate, swMateLOCK 16, compound gear, two gears on one shaft, concentric axes refused, coincident axes, swAddMateError_ErrorUknown, status 0, closest alignment, anti-aligned, UnfixComponent, GetConstrainedStatus, one degree of freedom, drive mate, angle mate linked to a global, CreateSelectData Mark, Select4 component]
answers: "How do I mate gears to their shafts and to each other from code so the whole gear train turns together at the right ratio and in the right direction?"
---

# Mate gears on their shafts into a train that turns

## What this is for

A gear train whose parts are only placed (or fixed) is a picture. To make it a
mechanism, each gear has to be held on its shaft so that it can only turn, each
meshing pair joined by a gear mate, and gears that share a shaft (a compound
gear) locked together. This entry is the set of mates that did that from code:
which mate holds a gear on a shaft axis and which one SolidWorks refuses, the
`AddMate5` argument order for a gear mate and which way it turns, the lock mate
for a compound gear, and how to tell that the result has exactly one degree of
freedom.

Everything below was measured on assemblies of plain cylinders (gear blanks
with a reference axis named `Gear Axis` made from their Top then Right planes)
and annuli standing in for ring gears, on shaft axes held by a body-less
skeleton part (planes driven by globals, one named axis per shaft). Lengths
cross COM in **metres** and angles in **radians**; the probe's helpers take
millimetres and degrees and convert at the call (`sc.m`, `math.radians`).

## The calls

All from the Gear-Generator probe's tier 8 (`p8_motion.py`), driven from Python
over pywin32 late binding. `call` is the late-bound helper
([connect/02](../connect/02-attach-from-python.md)), `sc.null()` a typed null
dispatch and `sc.out_long()` a by-reference long. Mate type and alignment
numbers were read from `swconst.tlb` at run time: `swMateCOINCIDENT` 0,
`swMateCONCENTRIC` 1, `swMateDISTANCE` 5, `swMateANGLE` 6, `swMateGEAR` 10,
`swMateLOCK` 16; `swMateAlignALIGNED` 0, `swMateAlignANTI_ALIGNED` 1,
`swMateAlignCLOSEST` 2; `swAddMateError_ErrorUknown` 0 (sic),
`swAddMateError_NoError` 1, `swAddMateError_OverDefinedAssembly` 5.

**One `AddMate5` for every mate**, on **IAssemblyDoc**, with what is selected:

```python
def add_mate(px: Px, asm: Any, label: str, kind: int, align: int, flip: bool = False, distance: float = 0.0,
             angle: float = 0.0, ratio: Tuple[float, float] = (1.0, 1.0), lock_rotation: bool = False) -> Dict[str, Any]:
    """``AddMate5`` on what is selected; what it returned, its error status, and the one new mate's name (or None).

    Distance in mm and angle in degrees; the argument order is the API help's:
    type, align, flip, distance and its two limits, the gear ratio's numerator
    and denominator, angle and its two limits, for-positioning-only, lock
    rotation, width option, error status.
    """
    before = [n for n, _ in _mate_features(asm)]
    d, a = sc.m(distance), math.radians(angle)
    status = sc.out_long()
    got, result = px.attempt(
        f"AddMate5 {label}",
        lambda: call(asm, "AddMate5", kind, align, flip, d, d, d, float(ratio[0]), float(ratio[1]), a, a, a, False,
                     lock_rotation, 0, status))
    call(asm, "ClearSelection2", True)
    mate = result[0] if got and isinstance(result, tuple) and result else result
    code = result[1] if got and isinstance(result, tuple) and len(result) > 1 else getattr(status, "value", None)
    made = [n for n, _ in _mate_features(asm) if n not in before]
    names = px.shared.get("mate_errors") or {}
    out = {"returned": (type(mate).__name__ if mate is not None else None) if got else "raised",
           "status": plain(code), "status_name": names.get(code) if isinstance(code, int) else None, "made": made,
           "name": made[0] if got and mate is not None and len(made) == 1 else None}
    if not got:
        out["error"] = plain(result)
    return out
```

`_mate_features` is the `MateGroup` walk of
[assemblies/02](02-mates-from-code.md). Every call returned the mate object
alone (never a tuple), and the status was read from the by-reference long's
`.value` afterwards.

**A gear is unfixed first.** Placed gears were fixed, as an assembly built from
frames leaves them ([assemblies/04](04-mates-between-non-parallel-axes.md)):

```python
def unfix(px: Px, asm: Any, component: Any) -> bool:
    if not bool(call(component, "IsFixed")):
        return True
    call(asm, "ClearSelection2", True)
    if not call(component, "Select4", False, sc.null(), False):
        return False
    px.attempt(f"UnfixComponent() on {call(component, 'Name2')}", lambda: asm.UnfixComponent())
    call(asm, "ClearSelection2", True)
    return not bool(call(component, "IsFixed"))
```

`UnfixComponent` on **IAssemblyDoc** takes no arguments, so like `FixComponent`
it is invoked with parentheses ([GOTCHAS §31](../../GOTCHAS.md)); `IsFixed`
read `False` afterwards. Unfixing did not move the gear (0 mm, 0 rotation).

### Holding a gear on its shaft

```python
def mount(px: Px, asm: Assembly, key: str, shaft: str, sigma: int, z_front: float, at: Sequence[float],
          record: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """Unfix gear ``key`` and mate it to ``"<shaft> Axis"`` and along it, the way shaft_axis_mates decided.

    Returns the mates' names (and adds what each AddMate5 answered to ``record``); a mate that was not made ends
    the probe.
    """
    enums = _enums(px)
    kind, axial = px.shared.get("axis_mate_route"), px.shared.get("axial_mate_route")
    if not kind or not axial:
        raise Require("shaft_axis_mates has not decided how a gear is held on its shaft.")
    gear, layout, doc = asm.gears[key], asm.layout, asm.doc
    if not unfix(px, doc, gear):
        raise Require(f"{key} would not unfix.")
    if kind == "face concentric":
        picked = select_face_at(px, doc, face_point(at, sigma), False, str(call(gear, "Name2")))
    else:
        picked = bool(select_in(px, doc, gear, "Gear Axis", "AXIS", False))
    if not (picked and select_in(px, doc, layout, f"{shaft} Axis", "AXIS", True)):
        raise Require(f"{key}'s axis and {shaft} Axis could not be selected.")
    mate_type = enums["coincident"] if kind == "axis coincident" else enums["concentric"]
    made = [add_mate(px, doc, f"{key} on {shaft} Axis", mate_type, enums["closest"])]
    if axial.startswith("origin"):
        picked = bool(_select_origin(px, doc, gear, append=False))
    else:
        picked = bool(select_in(px, doc, gear, _plane_names(gear)[0], "PLANE", False))
    if not (picked and select_in(px, doc, layout, _plane_names(layout)[0], "PLANE", True)):
        raise Require(f"{key}'s axial reference and the layout's Front could not be selected.")
    if abs(z_front) < 1e-9:
        made.append(add_mate(px, doc, f"{key} at 0 along {shaft}", enums["coincident"], enums["closest"]))
    else:
        made.append(add_mate(px, doc, f"{key} at {z_front:g} along {shaft}", enums["distance"], enums["closest"],
                             flip=axial.startswith("origin") and z_front < 0, distance=abs(z_front)))
    if record is not None:
        record.extend(made)
    names = [m["name"] for m in made]
    if None in names:
        raise Require(f"{key} was not mounted: {made}")
    return names
```

The route the probe settled on is `kind = "axis coincident"` and
`axial = "origin distance"`:

- **The gear's axis coincident with the shaft axis**: `AddMate5(0, 2, False, …)`
  with the component's `Gear Axis` and the skeleton part's `ShaftAxis1`
  selected at mark 1. **A concentric mate between the same two axes was
  refused**: `AddMate5(1, 2, …)` returned `None`, made nothing, and the status
  read **0** (`swAddMateError_ErrorUknown`), on shafts pointing +Z and −Z,
  both versions. The cylinder's outside *face* concentric with the shaft axis
  did hold.
- **Closest alignment keeps the side the gear was placed on.** On a +Z shaft
  `IMate2.Alignment` read 0, on a −Z shaft 1, and no gear turned over. Passed
  explicitly, `swMateAlignANTI_ALIGNED` turned a +Z gear over and
  `swMateAlignALIGNED` a −Z one.
- **Along the shaft, the gear's origin** (`Point1@Origin@<component>@<assembly>`,
  `EXTSKETCHPOINT`, as in [assemblies/04](04-mates-between-non-parallel-axes.md))
  at a distance from the skeleton's Front plane, `|z|` with `Flip` set when
  `z < 0` (a point's distance is along the plane's normal, GOTCHAS §42); a
  coincident mate when `z = 0`. That held gears at z = 5, −12 and 8 mm on +Z
  and −Z shafts. The gear's own Front *plane* at a distance from the
  skeleton's Front, `Flip` off, put it on the wrong side (12 and 14 mm off).
- What the two mates allow was checked by pushing each gear with a `Transform2`
  put and a rebuild: a 25° turn about its axis stayed; a 5 mm move off the axis,
  5 mm along it, and a 10° tilt all came back. Saved, closed and reopened, the
  mates and frames came back unchanged with no mate error.

`select_in` tries `IComponent2.FeatureByName` then `IFeature.Select2(append, 1)`,
then `SelectByID2("<feature>@<component>@<assembly>", "AXIS", …)`; all three
routes it knows selected the axes, including the third,
`IComponent2.GetCorresponding` of the part's own feature then
`IEntity.Select4(append, data)` with a select data whose `Mark` is 1:

```python
        elif route == SELECT_CORRESPONDING:
            def thunk() -> Any:
                part = call(component, "GetModelDoc2")
                entity = call(component, "GetCorresponding", sc.feature_by_name(part, name))
                data = call(call(asm, "SelectionManager"), "CreateSelectData")
                data.Mark = mark
                return call(entity, "Select4", append, data)
```

### A gear mate

With the first gear's `Gear Axis` selected, then the second's, both at mark 1:

```python
made = add_mate(px, doc, f"{name}: gear {ratio[0]}:{ratio[1]}", enums["gear"], enums[align], flip=flip,
                ratio=(float(ratio[0]), float(ratio[1])))
```

that is `AddMate5(10, 2, flip, 0, 0, 0, zFirst, zSecond, 0, 0, 0, False, False, 0, out)`,
with the **first selection's** tooth count as the numerator argument. It made
one `MateGearDim` (status 1).

- **The ratio goes first selection first.** With `(20, 40)` and the first gear
  driven 30°, the second turned 15°; with `(40, 20)`, 60°.
- **`Flip` False is the mesh's own sense.** Every external pair turned opposite
  ways with `Flip` False and the same way with `Flip` True: shafts +Z/+Z,
  +Z/−Z, −Z/+Z and −Z/−Z; the bigger count first or second; the two axes
  selected, the two outside faces, or one of each. A ring (an annulus round a
  cylinder) turned the **same** way as its pinion with `Flip` False, ring
  selected first or second, on +Z or −Z, axes or faces. So SolidWorks takes the
  sense from where the gears sit; give every meshing pair `Flip` False.
- **The alignment argument changed nothing.** Aligned, anti-aligned and
  closest gave the same turns, and `IMate2.Alignment` read 2 whatever was
  passed.
- **Read back, the ratio is the other way round.** `IFeature.GetDefinition`
  gave an `IGearMateFeatureData` whose `GearRatioNumerator` was the **second**
  selection's count and `GearRatioDenominator` the first's, in all 22 mates on
  both versions (`(20, 40)` read back numerator 40, denominator 20). That is
  [GOTCHAS §75](../../GOTCHAS.md) seen from the making side: `IMate2.MateEntity(0)`
  was the first-selected gear's axis and `MateEntity(1)` the second's in every
  one of the 22, so the numerator read back belongs to `MateEntity(1)`.
- **`Reverse` is not `Flip`.** What `IGearMateFeatureData.Reverse` read back
  matched `Flip`, inverted once when the two shafts pointed opposite ways and
  once for a ring, in every case measured. Read it as the mate's own bookkeeping,
  not as which way the pair turns.
- **Two of the skeleton's own axes were refused** as a gear mate's entities:
  `AddMate5` returned `None`, status 0.

### A lock mate for a compound gear

Two gears on one shaft that must turn together at a set angle to each other:
the first (the anchor) is held on the shaft as above; the second is unfixed and
**locked to the first, and not mated to the shaft itself**. A lock takes whole
components, selected like this:

```python
def select_components(px: Px, asm: Any, components: Sequence[Any]) -> Optional[str]:
    """Select whole components for a mate that takes them (a lock): with a mark-1 select data, else none."""
    for label in ("Select4 with a mark-1 select data", "Select4 with no select data"):
        call(asm, "ClearSelection2", True)
        ok = True
        for position, component in enumerate(components):
            before = sc.selected_count(asm)
            if label.startswith("Select4 with a mark"):
                data = call(call(asm, "SelectionManager"), "CreateSelectData")
                data.Mark = 1
            else:
                data = sc.null()
            got, value = px.attempt(f"{label}: {call(component, 'Name2')}",
                                    lambda c=component, d=data, a=position > 0: call(c, "Select4", a, d, False))
            if not (got and value and sc.selected_count(asm) > before):
                ok = False
                break
        if ok:
            return label
    call(asm, "ClearSelection2", True)
    return None
```

then

```python
result["select"] = select_components(px, doc, (p, q))
result["mate"] = add_mate(px, doc, f"{name}: lock", enums["lock"], enums["closest"])
```

that is `AddMate5(16, 2, False, 0, 0, 0, 1, 1, 0, 0, 0, False, False, 0, out)`.
The first route, `IComponent2.Select4(append, data, False)` with a
`ISelectionMgr.CreateSelectData` whose `Mark` was set to 1, selected both
components every time; the fallback was never needed.

The second gear placed 37° (and, in another pair, 137°) from the first:

| How the second gear was held | Result through drives of 30° and 90° more |
|---|---|
| Lock alone (not on the shaft) | **Held 37°**, on its axis, no mate error, +Z and −Z |
| Lock, and the second gear *also* on the shaft and along it | Held, but its axial and axis mates were flagged over-defined (`GetErrorCode2` 46 as a warning on 2026); on −Z both components read `GetConstrainedStatus` 4 |
| Angle mate between the two gears' Top planes, at 37° or 137° | Held, no error |
| 1 : 1 gear mate between the two axes, `Flip` False | Held |
| 1 : 1 gear mate, `Flip` True | **Slipped** (a coaxial pair is read as one gear inside the other) |

### One degree of freedom, and a drive

A finished train of two stages (four gears on three shafts, the middle shaft's
two gears locked, two gear mates) was checked with
`IComponent2.GetConstrainedStatus`, read through the probe's `member` helper
(property or method, whichever came back):

```python
def constrained(px: Px, component: Any) -> Any:
    """``IComponent2.GetConstrainedStatus``, as far as it answers (evidence only)."""
    got, value = px.attempt(f"GetConstrainedStatus of {call(component, 'Name2')}",
                            lambda: member(component, "GetConstrainedStatus")[0])
    return plain(value) if got else "raised"
```

Every gear read **2** (under-defined) once mated. One angle mate between the
input gear's Top plane and a skeleton plane (its Top plane at 10° in one probe,
its Right plane at 90° in another), its `D1` linked to an assembly global
([equations/02](../equations/02-link-a-dimension-to-a-global.md)), made
**every** gear read **3** (fully defined): the train has exactly one degree of
freedom. Adding the drive moved no gear. Changing that global by 30° and
rebuilding turned the input 30° and
the output by exactly the product of the two stage ratios, the same way as the
input, on a train with every shaft +Z and on one whose middle shaft pointed
−Z; saved, reopened and driven again, the same. The drive's own sense: the
angle growing from 90° to 120° turned a +Z input +30° about +Z, and setting it
back to 90° returned every gear to its built frame (to about 3e-14 mm). With
the link equation deleted (`IEquationMgr.Delete`) and the angle mate deleted
([assemblies/02](02-mates-from-code.md#deleting-a-mate)), every frame stayed
where it was and every gear read 2 again.

That is also the first observation in this collection of an **angle** mate
following its global; [assemblies/02](02-mates-from-code.md) had only seen the
link accepted.

## Why it is not obvious

- **Concentric is the obvious mate and it is refused** between two reference
  axes, with status 0 and no other message. Use coincident.
- **The ratio is put first-selection-first and read back reversed.** A tool
  that writes the ratio it read back makes the inverse ratio.
- **`Flip` is not "external versus internal".** It needs no special case for a
  ring gear; a tool that flips for a ring makes the ring turn against its
  pinion. A ring and pinion with real teeth built that way, `Flip` True, turned
  at −3 : 1 instead of 3 : 1 and showed four interferences
  ([assemblies/03](03-interference-detection.md)); SolidWorks 2026, a build
  script's log rather than a probe.
- **A locked gear is not also mated to its shaft.** It looks harmless and
  over-defines the assembly, with only warnings on 2026 (see
  [assemblies/02](02-mates-from-code.md#when-a-mate-is-refused-or-over-defines)
  for what over-definition looks like).
- **Neither a drag nor a placement turns the train.** With the drive suppressed,
  turning the input by a `Transform2` put, by `IComponent2.SetTransformAndSolve2`
  or through `IDragOperator` (`Drag`, `DragAsUI`, several settings; every call
  returned `True`) turned the input alone; see
  [assemblies/05](05-test-motion-with-the-drag-operator.md). The gear mates
  were proved by driving a mate through a global instead.

## What it does not do

- Only cylinders and annuli were mated: no tooth geometry was involved in any
  sense or ratio reading. Real gears were mated the same way by the tool
  afterwards, but those runs are not the evidence here.
- Lightweight components were not tried.
- The sense rule was fitted to placements a meshing pair can have. Of three
  placements no meshing pair has, recorded beside it, one did **not** fit: a
  pinion inside a ring's bore but moved along the axis clear of the ring's face
  turned opposite to the ring, as an external pair does. (An external pair moved
  apart along the axis, and a pinion placed outside its ring, both turned
  opposite ways too.)
- Gear mates between non-parallel axes (bevel, crossed) were not tried this
  way.
- `GetConstrainedStatus` 4 was observed (over-defined) here, unlike on
  `ISketch` ([sketches/10](../sketches/10-is-the-sketch-fully-defined.md)).

## Evidence

Gear-Generator probe tier 8 (`shaft_axis_mates`, `gear_mate_sense`,
`compound_lock`, `mated_train`, and `demonstration_drive` for the drive's
sense), Python over pywin32 late binding:

- SolidWorks 2026 revision 34.0.0, full run 20261113-231301 (75 of 75 passed),
  and revision 34.1.1, full run 20261114-034458 (83 of 83).
- SolidWorks 2024 SP5 (32.5.0), tier 8 in run 20261113-223412 (31 of 31) in a
  freshly started session; `demonstration_drive` in run 20261114-040636 (see
  [assemblies/11](11-change-a-mated-gear-train.md) for that run's caveat).
- Every decision was the same on both versions; the only difference was the
  numbers `GetErrorCode2` gave for flagged mates (46/47 on 2026, 51 on 2024).

Readings, both versions unless said:

- `shaft_axis_mates`: `axis_mate_types_holding = {'axis coincident': True, 'axis concentric': False, 'face concentric': True}`;
  the refused concentric mates `{'made': [], 'returned': None, 'status': 0, 'status_name': 'swAddMateError_ErrorUknown'}`;
  `axial_routes_holding = {'front plane distance': False, 'origin coincident': True, 'origin distance': True}`;
  `closest_keeps_the_side` true for all six gears; `explicit_alignment` turned
  both gears over; `axis_select_routes` true for all three routes; after the
  reopen every frame 0.0 mm / 0.0 off, no mate error.
- `gear_mate_sense`, 22 pairs in batches of five to an assembly, driven 30°
  from 10° to 40° by one global: `sense_rules_consistent = ['mesh']`;
  `alignment_changes_sense = False`, alignment read back 2 in all 22; every
  definition read the second count as `GearRatioNumerator`; `MateEntity(0)` the
  first-selected component in all 22; e.g. `(20, 40)`, `Flip` False: turns
  `own_a 30.0, own_b -15.0`; `(40, 20)`: `own_b -60.0`; the skeleton's own axes:
  `{'returned': None, 'status': 0}`.
- `compound_lock`: `lock_routes_holding = {'angle': True, 'lock alone': True, 'lock both': False}`;
  the lock alone `relative 37.0` after both drives, status 1, selected by
  `"Select4 with a mark-1 select data"`; the 1 : 1 gear mate with `Flip` True
  read `relative -23.0` then `157.0`.
- `mated_train`: `one_drive_fully_defines_the_train = True`
  (`constrained_mated` all 2, `constrained_driven` all 3); both trains turned
  the right way at the expected ratio to 1e-6; no gear moved when mated from its
  fixed placement (0 mm, 0 rotation).
- `demonstration_drive`: `demonstration_drive_sense = 1` on both trains; after
  deleting the drive, the worst frame error was 2.7e-12 mm.

The result files are kept in the Gear-Generator repository, not here.

## See also

- [assemblies/02 — Mates from code](02-mates-from-code.md) — `AddMate5`, failing and over-defining mates, deleting and renaming
- [assemblies/04 — Mates between non-parallel axes](04-mates-between-non-parallel-axes.md) — placing by frame, the origin point, `Flip` on a point distance
- [assemblies/05 — Test motion with the drag operator](05-test-motion-with-the-drag-operator.md) — why a drag did not turn this train
- [assemblies/06 — Read every mate](06-read-every-mate.md) — reading gear mates back; `MateEntity` order
- [assemblies/11 — Change a mated gear train](11-change-a-mated-gear-train.md) — re-phasing, locks, and a new ratio
- [assemblies/12 — Rebuild an assembly without marking every part modified](12-rebuild-scope-and-the-save-flag.md)
- [assemblies/03 — Interference detection](03-interference-detection.md)
- [equations/02 — Link a dimension to a global](../equations/02-link-a-dimension-to-a-global.md)
- [GOTCHAS §31, §42, §75, §94, §95, §96, §98](../../GOTCHAS.md)
