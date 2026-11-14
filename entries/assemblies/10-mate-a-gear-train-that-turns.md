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
millimetres and degrees and converted at the call; the listings here take metres and radians.

## The calls

From the Gear-Generator probe's tier 8 (`p8_motion.py`), driven from Python
over pywin32 late binding ([connect/02](../connect/02-attach-from-python.md)).
The listings below are copied from [`code/python/gear_train/gear_train_check.py`](../../code/python/gear_train/gear_train_check.py), a self-contained runner that
builds plain-cylinder fixtures and repeats these calls, the same SolidWorks
calls, arguments and order as the probe. It ran on SolidWorks 2026 (34.1.1) and 2024 SP5 (32.5.0), each started fresh by the runner (results `gear-train-check-20261114-140356` and `gear-train-check-20261114-140631` beside it). The first listing defines the
small helpers the rest use. Mate type and alignment
numbers were read from `swconst.tlb` at run time: `swMateCOINCIDENT` 0,
`swMateCONCENTRIC` 1, `swMateDISTANCE` 5, `swMateANGLE` 6, `swMateGEAR` 10,
`swMateLOCK` 16; `swMateAlignALIGNED` 0, `swMateAlignANTI_ALIGNED` 1,
`swMateAlignCLOSEST` 2; `swAddMateError_ErrorUknown` 0 (sic),
`swAddMateError_NoError` 1, `swAddMateError_OverDefinedAssembly` 5.

**One `AddMate5` for every mate**, on **IAssemblyDoc**, with what is selected:

```python
import pythoncom
from win32com.client import VARIANT

COINCIDENT, CONCENTRIC, DISTANCE, ANGLE, GEAR, LOCK = 0, 1, 5, 6, 10, 16
CLOSEST = 2


def call(obj, name, *args):
    """Late-bound member: invoked when given arguments, read by attribute access otherwise."""
    member = getattr(obj, name)
    return member(*args) if args else member


def null():
    return VARIANT(pythoncom.VT_DISPATCH, None)              # a typed Nothing


def out_long():
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)  # a by-reference long


def selected_count(doc):
    return int(call(call(doc, "SelectionManager"), "GetSelectedObjectCount2", -1) or 0)


def top_features(doc):
    out, feature = [], call(doc, "FirstFeature")
    while feature is not None:
        out.append(feature)
        feature = call(feature, "GetNextFeature")
    return out


def mate_features(asm):
    """The sub-features of the MateGroup, in walk order."""
    out = []
    for feature in top_features(asm):
        if call(feature, "GetTypeName2") == "MateGroup":
            child = call(feature, "GetFirstSubFeature")
            while child is not None:
                out.append(child)
                child = call(child, "GetNextSubFeature")
    return out


def mate_feature(asm, name):
    return next(f for f in mate_features(asm) if str(call(f, "Name")) == name)


def add_mate(asm, kind, align, flip=False, distance_m=0.0, angle_rad=0.0, ratio=(1.0, 1.0)):
    """IAssemblyDoc.AddMate5 on what is selected at mark 1: type, align, flip, distance and its two
    limits, the gear ratio's numerator and denominator, angle and its two limits, for-positioning-only,
    lock rotation, width option, error status. Returns (mate, status, names of the new mates)."""
    before = {str(call(f, "Name")) for f in mate_features(asm)}
    d, a = distance_m, angle_rad
    status = out_long()
    mate = call(asm, "AddMate5", kind, align, flip, d, d, d, float(ratio[0]), float(ratio[1]),
                a, a, a, False, False, 0, status)
    call(asm, "ClearSelection2", True)
    made = [str(call(f, "Name")) for f in mate_features(asm) if str(call(f, "Name")) not in before]
    return mate, status.value, made


def rename(feature, name):
    """An IFeature.Name put, read back: SolidWorks renames quietly on a collision."""
    feature.Name = name
    return str(call(feature, "Name"))
```

`mate_features` is the `MateGroup` walk of
[assemblies/02](02-mates-from-code.md). Every call returned the mate object
alone (never a tuple), and the status was read from the by-reference long's
`.value` afterwards. The probe passed distances in millimetres and angles in
degrees to its own helper and converted them at the call; here they are given
in metres and radians directly.

**A gear is unfixed first.** Placed gears were fixed, as an assembly built from
frames leaves them ([assemblies/04](04-mates-between-non-parallel-axes.md)):

```python
def unfix(asm, component):
    """Select the component, then IAssemblyDoc.UnfixComponent() with parentheses."""
    if not call(component, "IsFixed"):
        return True
    call(asm, "ClearSelection2", True)
    if not call(component, "Select4", False, null(), False):
        return False
    asm.UnfixComponent()           # reached by attribute access alone it would only be fetched
    call(asm, "ClearSelection2", True)
    return not call(component, "IsFixed")
```

`UnfixComponent` on **IAssemblyDoc** takes no arguments, so like `FixComponent`
it is invoked with parentheses ([GOTCHAS §31](../../GOTCHAS.md)); `IsFixed`
read `False` afterwards. Unfixing did not move the gear (0 mm, 0 rotation).

### Holding a gear on its shaft

```python
def select_feature_of(asm, component, name, append, mark=1):
    """A component's plane or axis: IComponent2.FeatureByName, then IFeature.Select2(append, mark);
    else SelectByID2("<feature>@<component>@<assembly>")."""
    if not append:
        call(asm, "ClearSelection2", True)
    before = selected_count(asm)
    feature = call(component, "FeatureByName", name)
    if feature is not None and call(feature, "Select2", append, mark) and selected_count(asm) > before:
        return True
    kind = "AXIS" if feature is not None and call(feature, "GetTypeName2") == "RefAxis" else "PLANE"
    assembly = str(call(asm, "GetTitle")).rsplit(".", 1)[0]
    full = f"{name}@{call(component, 'Name2')}@{assembly}"
    return bool(call(call(asm, "Extension"), "SelectByID2", full, kind, 0.0, 0.0, 0.0, append, mark,
                     null(), 0)) and selected_count(asm) > before


def select_origin(asm, component, append, mark=1):
    """Point1@<origin feature>@<component>@<assembly>, as an EXTSKETCHPOINT (assemblies/04)."""
    part = call(component, "GetModelDoc2")
    origin = next(str(call(f, "Name")) for f in top_features(part)
                  if call(f, "GetTypeName2") == "OriginProfileFeature")
    assembly = str(call(asm, "GetTitle")).rsplit(".", 1)[0]
    if not append:
        call(asm, "ClearSelection2", True)
    before = selected_count(asm)
    full = f"Point1@{origin}@{call(component, 'Name2')}@{assembly}"
    return bool(call(call(asm, "Extension"), "SelectByID2", full, "EXTSKETCHPOINT", 0.0, 0.0, 0.0,
                     append, mark, null(), 0)) and selected_count(asm) > before


def hold_on_shaft(asm, gear, skeleton, shaft_axis, skeleton_front, z_front_m):
    """Unfix a gear, put its Gear Axis on the skeleton's shaft axis, and hold its origin
    z_front_m (metres, signed) from the skeleton's Front plane. Returns each AddMate5's answer."""
    if not unfix(asm, gear):
        raise RuntimeError("the gear would not unfix")
    if not (select_feature_of(asm, gear, "Gear Axis", False) and
            select_feature_of(asm, skeleton, shaft_axis, True)):
        raise RuntimeError("the two axes could not be selected")
    made = [add_mate(asm, COINCIDENT, CLOSEST)]
    if not (select_origin(asm, gear, False) and select_feature_of(asm, skeleton, skeleton_front, True)):
        raise RuntimeError("the origin and the Front plane could not be selected")
    if abs(z_front_m) < 1e-12:
        made.append(add_mate(asm, COINCIDENT, CLOSEST))
    else:   # a point's distance is along the plane's normal: Flip for the negative side (GOTCHAS §42)
        made.append(add_mate(asm, DISTANCE, CLOSEST, flip=z_front_m < 0, distance_m=abs(z_front_m)))
    return made
```

`skeleton_front` is the name of the skeleton part's first plane, read from its
tree. That is the route the probe settled on, after trying the others below:

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

The probe selected the axes three ways, and all three worked on both
versions: `select_feature_of` above; `SelectByID2("<feature>@<component>@<assembly>", "AXIS", 0, 0, 0, append, 1, null, 0)`
on the assembly's extension; and `IComponent2.GetCorresponding` of the part's
own feature, then `Select4(append, data)` on what it returned (its interface was
not checked) with a select data whose `Mark` is 1:

```python
def select_by_corresponding(asm, component, feature_name, append, mark=1):
    """The assembly's instance of one of the part's features, selected at a mark."""
    if not append:
        call(asm, "ClearSelection2", True)
    part = call(component, "GetModelDoc2")
    feature = next(f for f in top_features(part) if str(call(f, "Name")) == feature_name)
    entity = call(component, "GetCorresponding", feature)
    data = call(call(asm, "SelectionManager"), "CreateSelectData")
    data.Mark = mark
    return bool(call(entity, "Select4", append, data))
```

### A gear mate

With the first gear's `Gear Axis` selected, then the second's, both at mark 1:

```python
select_feature_of(asm, gears[first], "Gear Axis", False)
select_feature_of(asm, gears[second], "Gear Axis", True)
mate, status, made = add_mate(asm, GEAR, CLOSEST, flip=False, ratio=(TEETH[first], TEETH[second]))
```

(lines from the runner's train step: `gears` holds its components, `TEETH` each
gear's illustrative tooth count), that is
`AddMate5(10, 2, flip, 0, 0, 0, zFirst, zSecond, 0, 0, 0, False, False, 0, out)`,
with the **first selection's** tooth count as the numerator argument (the probe
also tried `Flip` True, faces in place of axes, and explicit alignments, below). It made
one `MateGearDim` (status 1).

- **The ratio goes first selection first.** With `(20, 40)` and the first gear
  driven 30°, the second turned 15°; with `(40, 20)`, 60°.
- **`Flip` False was right for every external pair and every plain annulus.**
  Every external pair turned opposite ways with `Flip` False and the same way
  with `Flip` True: shafts +Z/+Z, +Z/−Z, −Z/+Z and −Z/−Z; the bigger count first
  or second; the two axes selected, the two outside faces, or one of each. A
  pinion inside a plain annulus (no teeth) turned the **same** way as the
  annulus with `Flip` False, annulus selected first or second, on +Z or −Z,
  axes or faces. Both versions.
- **But no static rule holds for a toothed internal ring gear.** A later probe
  round mated pinions inside real toothed ring gears (spur, and 20° helical) on
  every combination of shaft senses, either gear selected first. The `Flip` a
  pair needed to turn as it meshes was **opposite on SolidWorks 2026 and 2024**
  for every toothed ring, and on each version, on opposite-sense shafts, it
  differed between the spur rings and the helical ones; which gear was selected
  first never changed it. The plain annulus and an external pair needed `Flip`
  False on both versions, which is how the first round, on annuli, missed it.
  A follow-up round found the same for other ring geometries: helical rings
  of the other hand and of 15°, a herringbone ring and a spur ring with a
  shifted pinion each needed opposite `Flip` on the two versions (the helical
  and herringbone rings one way, the spur rings the other), though these were
  tried on one shaft-sense combination only, pinion +Z and ring −Z. An external
  pair needed `Flip` False on both versions with both shafts +Z, both −Z, and
  on opposite senses either way round. So
  nothing known before the mate is made (inside or outside, both shaft senses,
  which gear first, spur or helical) gives the right `Flip` on both versions.
  **Read the made mate back instead** ([below](#checking-a-gear-mates-sense-after-making-it)).
- **The alignment argument changed nothing.** Aligned, anti-aligned and
  closest gave the same turns, and `IMate2.Alignment` read 2 whatever was
  passed.
- **Read back, the ratio is the other way round.** `IFeature.GetDefinition`
  gave an `IGearMateFeatureData` whose `GearRatioNumerator` was the **second**
  selection's count and `GearRatioDenominator` the first's, in all 22 mates on
  both versions (`(20, 40)` read back numerator 40, denominator 20). That is
  [GOTCHAS §75](../../GOTCHAS.md) seen from the making side: `IMate2.MateEntity(0)`
  was the first-selected gear's entity (its axis, or its face where faces were
  selected) and `MateEntity(1)` the second's in every one of the 22, so the
  numerator read back belongs to `MateEntity(1)`.
- **`Reverse` is not `Flip`.** In the 15 meshing pairs mated by their axes,
  what `IGearMateFeatureData.Reverse` read back was `Flip`, inverted once when
  the two shafts pointed opposite ways and once for a ring; the three pairs
  mated by their faces fitted the same rule. Three did **not**: the pair mated
  by one axis and one face, a pinion moved along its ring's axis clear of the
  ring, and a pinion placed outside its ring (each read `False` where the rule
  gives `True`). On its own `Reverse` does not say which way the pair turns;
  together with the entities' directions it does (next section).
- **Two of the skeleton's own axes were refused** as a gear mate's entities:
  `AddMate5` returned `None`, status 0.

### Checking a gear mate's sense after making it

What SolidWorks reports once the mate is made does tell which way it turns:

```python
def gear_mate_sense_read_back(asm, name, internal):
    """Whether a made gear mate turns its gears as they mesh, read back: exactly when
    (IGearMateFeatureData.Reverse == its two MateEntity directions point the same way) == internal."""
    feature = mate_feature(asm, name)
    reverse = bool(call(call(feature, "GetDefinition"), "Reverse"))
    mate = call(feature, "GetSpecificFeature2")
    d0, d1 = [list(call(call(mate, "MateEntity", i), "EntityParams"))[3:6] for i in (0, 1)]
    parallel = sum(a * b for a, b in zip(d0, d1)) > 0
    return (reverse == parallel) == internal, {"Reverse": reverse, "parallel": parallel}
```

`internal` is whether one gear is inside the other (a pinion in a ring), which
the tool knows. `Reverse` is read through `IFeature.GetDefinition`
(`IGearMateFeatureData`); the directions are items 3–5 of each
`IMateEntity2.EntityParams` ([assemblies/06](06-read-every-mate.md)). In the
probe round's 52 mates on each version (toothed spur rings, one 20° helical
ring geometry, plain annuli, every shaft sense for the rings, an external pair
on opposite-sense shafts, either gear first, `Flip` False and True) this
read-back agreed with the measured turn every time: the two versions
store a different `Reverse` for the same toothed-ring call, and the read-back
follows what each decided. Driven 10° off the built phase, every toothed pair
whose sense was wrong clashed (3 interferences for a spur ring, 4 for a helical
ring, 2 for an external pair) and every right one stayed clear. A wrong sense is
corrected by deleting the mate and adding it again with the other `Flip`
([assemblies/11](11-change-a-mated-gear-train.md)).

A follow-up probe round, on three tool-built trains with 13 gear mates on each
version, settled when the read can be taken and what it costs:

- **The read marks nothing.** On reopened trains with every document's
  `GetSaveFlag` False, each gear mate was read (`GetDefinition` for `Reverse`
  and the ratio, then `GetSpecificFeature2`, `MateEntity(0)` and `(1)`,
  `EntityParams`), with every save flag read straight before and after. No
  flag changed on the assembly, the skeleton or any part, on either version.
  So the sense can be checked before anything is changed.
- **Any read point gives the same answer.** Read straight after the `AddMate5`
  calls, after a top-only rebuild, straight after a delete-and-remake, and after
  a save, close and reopen, each mate told the sense a drive then found, on
  both versions.
- **It holds under `CommandInProgress`.** Made, read, deleted and made again
  with the other `Flip` with `CommandInProgress` True and no rebuild between,
  the remade mate's read equalled its read after the rebuild and told the
  drive's sense, on both versions. Two limits: the mate first made under it was
  deleted before any drive, so its read is right by comparison (the same read
  with `CommandInProgress` off, and the opposite of the remade mate's), not by a
  drive; and the remake from a wrong mate to a right one under it was shown on
  2026 only (on 2024 it only went from right to wrong).
- **The sense crosses versions in one direction tested.** Trains mated right on
  2024 and opened in 2026 kept the `Reverse` 2024 stored; the read-back said
  right and a drive turned all 13 meshes right with no clash, with no remake.
  2026 does not re-decide the sense on open. The other direction cannot be
  tried: 2024 cannot open a 2026 file. Closing such an assembly in 2026 after
  changing it can raise the CAM add-in's box ([GOTCHAS §100](../../GOTCHAS.md)).

### A lock mate for a compound gear

Two gears on one shaft that must turn together at a set angle to each other:
the first (the anchor) is held on the shaft as above; the second is unfixed and
**locked to the first, and not mated to the shaft itself**. A lock takes whole
components, selected like this:

```python
def select_components(asm, components):
    """Whole components at mark 1: IComponent2.Select4(append, data, False) with data.Mark = 1."""
    call(asm, "ClearSelection2", True)
    for position, component in enumerate(components):
        before = selected_count(asm)
        data = call(call(asm, "SelectionManager"), "CreateSelectData")
        data.Mark = 1
        if not (call(component, "Select4", position > 0, data, False) and selected_count(asm) > before):
            return False
    return True
```

then

```python
s.fact("lock selection", select_components(asm, (gears["GearB"], gears["GearC"])))
mate, status, made = add_mate(asm, LOCK, CLOSEST)
```

(from the runner's step, where `s.fact` records a reading), that is
`AddMate5(16, 2, False, 0, 0, 0, 1, 1, 0, 0, 0, False, False, 0, out)`.
`IComponent2.Select4(append, data, False)` with an
`ISelectionMgr.CreateSelectData` whose `Mark` was set to 1 selected both
components every time; the probe's fallback (`Select4` with a null select data)
was never needed.

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
`IComponent2.GetConstrainedStatus`, read as the probe read it (by attribute
access, and called only if a method came back):

```python
def constrained_status(component):
    """2 under-defined, 3 fully defined, 4 over-defined (swConstrainedStatus_e)."""
    value = call(component, "GetConstrainedStatus")
    return value() if type(value).__name__ == "method" else value
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

### Mating under CommandInProgress

The whole mate set of such a train (18 `AddMate5` calls, each mate renamed
straight after it) was also made with `ISldWorks.CommandInProgress` set `True`
and a single `ForceRebuild3(True)` at the end: every status 1, every mate code 0,
no gear moved, and one drive then defined the train and turned it at its ratio,
on both versions ([assemblies/12](12-rebuild-scope-and-the-save-flag.md#what-each-rebuild-marked)).

## Why it is not obvious

- **Concentric is the obvious mate and it is refused** between two reference
  axes, with status 0 and no other message. Use coincident.
- **The ratio is put first-selection-first and read back reversed.** A tool
  that writes the ratio it read back makes the inverse ratio.
- **No fixed `Flip` is right for a toothed ring gear on both versions.**
  Annuli without teeth, which is what a first test is likely to use, all take
  `Flip` False, and so do external pairs; toothed rings took opposite values on
  2026 and 2024. Make the mate, read it back, and remake it with the other
  `Flip` if the read-back says the sense is wrong. A wrong sense looks like
  this: a toothed ring and pinion on 2026 with the wrong `Flip` turned at
  −3 : 1 instead of 3 : 1 and showed four interferences
  ([assemblies/03](03-interference-detection.md); a build script's log).
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

- The first round mated only cylinders and annuli: no tooth geometry was
  involved in its sense or ratio readings. The later ring round mated toothed
  spur rings and one 20° helical ring geometry, and a follow-up round further
  helical, herringbone and shifted-pinion spur rings, these on one shaft-sense
  combination only (see the `Flip` bullets above). Internal gears other than
  toothed rings on parallel shafts, and other gear kinds, were not tried.
- Mating was measured with every component fully resolved. With the
  components forced lightweight, the train's first drive read one gear far from
  where it should be (possibly a stale transform read while lightweight); read
  `GetSuppression2` on every component and require 2 before reading transforms,
  driving or changing a train
  ([assemblies/11](11-change-a-mated-gear-train.md#with-the-components-lightweight)).
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
  freshly started session; `demonstration_drive` in run 20261114-071324, also
  a fresh session.
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

- The toothed ring gears and the read-back: probe `ring_mate_sense`,
  SolidWorks 2026 34.1.1 (run 20261114-133014) and 2024 SP5 (run
  20261114-135104), each in a fresh session, 52 mates each: the read-back agreed
  with the measured turn in all 52 on both; `ring_sense_needed_flip_annulus` all
  `False` on both; the needed `Flip` for toothed rings opposite between the two
  files for every shaft combination where it was defined.
- The read-back's footing: probes `ring_trains_saved` (SolidWorks 2024 SP5 run
  20261114-151013, SolidWorks 2026 34.1.1 run 20261114-162034) and
  `ring_trains_from_another_version` (the 2024-saved trains opened in 2026, run
  20261114-162546), each in a fresh session, 3 trains and 13 gear mates: no
  save flag changed across any read; the read agreed with the drive at every
  read point; the remade mate's read under `CommandInProgress` equalled its read
  after the rebuild; the needed `Flip` for the further helical, herringbone and
  shifted-pinion spur rings opposite between the versions, and `False` for the
  external pair in every shaft sense; after a ratio remake, a ring mesh that
  read wrong on 2026 was remade with the other `Flip` and then read and turned
  right (it was driven only after that second remake); on 2026, the 2024 trains
  read `GetSaveFlag` False on open and after the read-back and turned right.
  The two versions' runs came from different probe revisions, differing only in
  how the remake verdict is judged; the raw readings agree.

- The listings themselves, on four plain cylinders and a skeleton: the gear-train runner ([`code/python/gear_train/`](../../code/python/gear_train/README.md)), results `gear-train-check-20261114-140356` (SolidWorks 2026 34.1.1) and `gear-train-check-20261114-140631` (2024 SP5 32.5.0), 25 of 25 steps each.
  Both versions: the concentric mate between two axes `{'returned': None, 'status': 0}`;
  every shaft, lock and gear mate status 1, every mate code 0, every gear
  `GetConstrainedStatus` 2, then 3 with the drive; no gear moved when mated;
  the ratio passed `(20, 40)` read back `[40.0, 20.0]` with `MateEntity(0)` the
  first gear; driven 30°, turns `{'GearA': 30.0, 'GearB': -15.0, 'GearC': -15.0, 'GearD': 6.0}`;
  the sense read-back `True` for both external mates; a pinion in a plain
  annulus turned the same way with `Flip` False (read-back `True`) and the
  opposite way with `Flip` True (read-back `False`).

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
