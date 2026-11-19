---
schema: 2
id: assemblies-11-change-a-mated-gear-train
title: Change a mated gear train in place — re-phase a gear, move a shaft, re-take a lock, change a gear mate's ratio
answers: "My gear train is mated and turns; how do I change it from code afterwards — turn one gear to a new phase, move a shaft, change a compound gear's angle or position, or give a gear mate a new ratio — without breaking the mates?"
keywords: [change gear ratio, gear mate ratio, ModifyDefinition gear mate, IGearMateFeatureData put, AccessSelections AttributeError, 0x80010105, server threw an exception, CloseDoc cannot close, assembly will not close, remake gear mate, delete and re-add mate, lock mate re-take, suppress lock, re-phase gear, mesh phase, Transform2 put with gear mate, lock does not hold against put, shaft moved by globals, skeleton part, axial distance global, tooth count change, idler gear, remade mate goes last, half pitch interference control, lightweight, GetSuppression2, swComponentFullyResolved, first drive wrong while lightweight, LoadLightweight, OverrideDefaultLoadLightweight, SOLIDWORKS CAM Error]
api: [IComponent2.Transform2, IFeature.SetSuppression2, IFeature.IsSuppressed2, IFeature.GetDefinition, IFeature.ModifyDefinition, IGearMateFeatureData.GearRatioNumerator, IGearMateFeatureData.GearRatioDenominator, IModelDoc2.EditDelete, IAssemblyDoc.GetComponentByName, IAssemblyDoc.AddMate5, ISldWorks.CloseDoc, ISldWorks.OpenDoc6, IComponent2.GetSuppression2]
language: [python]
status: verified
verified_on: SolidWorks 2026 (revisions 34.0.0 and 34.1.1) and SolidWorks 2024 SP5 (32.5.0), each in a session started fresh for the run
majors: [32, 34]
evidence: []
recipe_status: null
recipe_evidence: []
superseded_by: null
---

# Change a mated gear train in place

## What this is for

A gear train mated as in [assemblies/10](10-mate-a-gear-train-that-turns.md)
has one degree of freedom, so moving any one gear by hand fights the mates. A
tool that updates such a train (a shaft moved, a gear's phase or position along
its shaft changed, a tooth count changed) needs to know which edits the mates
take, which they silently ignore, and which leave the assembly in a state
SolidWorks cannot recover from. This entry is what was measured, on trains of
two stages (an input gear, a compound pair locked together on the middle
shaft, and an output gear; gear mates with `Flip` False) on a body-less
skeleton part whose planes and shaft axes are driven by globals.

Lengths cross COM in **metres**, angles in **radians**; the probe's helpers take
millimetres and degrees. Every rebuild below is `ForceRebuild3(True)` unless
said ([assemblies/12](12-rebuild-scope-and-the-save-flag.md)).

## The calls

From the Gear-Generator probe's tier 8 (`p8_motion.py`), Python over pywin32
late binding. A "put" below is the `Transform2` put of
[assemblies/04](04-mates-between-non-parallel-axes.md) followed by a rebuild.
The listings are copied from [`code/python/gear_train/gear_train_check.py`](../../code/python/gear_train/gear_train_check.py), a self-contained runner with the
probe's calls, arguments and order. It ran on SolidWorks 2026 (34.1.1) and 2024 SP5 (32.5.0), each started fresh by the runner (results `gear-train-check-20261114-140356` and `gear-train-check-20261114-140631` beside it). The definition route is the exception:
its listing below is condensed from the probe and was not run as written (it
leaves out the probe's `AccessSelections` call, which raised every time), since
on SolidWorks 2024 that route leaves an assembly that cannot be closed.

**Helpers**, the same as in [assemblies/10](10-mate-a-gear-train-that-turns.md#the-calls):

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
```

**Suppressing and unsuppressing one mate**, judged by reading the state back:

```python
SUPPRESS, UNSUPPRESS, THIS_CONFIGURATION = 0, 1, 1


def is_suppressed(feature):
    """IFeature.IsSuppressed2 in this configuration (one flag per configuration asked for)."""
    value = call(feature, "IsSuppressed2", THIS_CONFIGURATION, null())
    value = value[0] if isinstance(value, tuple) else value
    return bool(value[0] if isinstance(value, (list, tuple)) else value)


def set_suppressed(asm, name, on):
    feature = mate_feature(asm, name)
    call(feature, "SetSuppression2", SUPPRESS if on else UNSUPPRESS, THIS_CONFIGURATION, None)
    call(asm, "ClearSelection2", True)
    return is_suppressed(feature) is on
```

`swFeatureSuppressionAction_e` `swSuppressFeature` 0 / `swUnSuppressFeature` 1
and `swInConfigurationOpts_e` `swThisConfiguration` 1, read from `swconst.tlb`.
The probe kept two fallbacks behind this call (a typed null in place of
`None`, and `Select2` then `EditSuppress2()` / `EditUnsuppress2()`), and fell
back to `IsSuppressed` if `IsSuppressed2` raised. **`IFeature.SetSuppression2(action, 1, None)`
did it every time**, for gear mates, locks and angle mates, both ways, on both
versions; neither fallback was needed.

**Changing a gear mate's ratio through its definition:**

```python
def set_gear_ratio_by_definition(asm, name, z_first, z_second):
    """IFeature.GetDefinition of a gear mate, both ratio fields put, IFeature.ModifyDefinition."""
    feature = mate_feature(asm, name)
    data = call(feature, "GetDefinition")                 # an IGearMateFeatureData
    data.GearRatioNumerator = float(z_first)              # AddMate5's order, not the order it reads back in
    data.GearRatioDenominator = float(z_second)
    return call(feature, "ModifyDefinition", data, asm, null())
```

The probe called `AccessSelections(asm, null)` on the definition first; it
raised `AttributeError` every time, and `ModifyDefinition` worked without it.
The way of filling the fields that gave the right ratio puts the two counts
**in `AddMate5`'s order** (first selection's count in `GearRatioNumerator`),
although `GetDefinition` reads them back the other way round
([assemblies/10](10-mate-a-gear-train-that-turns.md#a-gear-mate)). The probe
also tried putting the new count into the field that held the old one, alone and
with the other field as read; both made the inverse ratio.

**Changing it by deleting the gear mate and making it again** ("remake"):

```python
def delete_mate(asm, name):
    """Select the mate, then IModelDoc2.EditDelete() with parentheses; judged by the tree."""
    feature = next((f for f in mate_features(asm) if str(call(f, "Name")) == name), None)
    if feature is None:
        return False
    call(asm, "ClearSelection2", True)
    call(feature, "Select2", False, 0)
    asm.EditDelete()               # attribute access alone would only fetch it
    call(asm, "ClearSelection2", True)
    return all(str(call(f, "Name")) != name for f in mate_features(asm))


def remake_gear_mate(asm, name, first_component, second_component, z_first, z_second):
    """Delete a gear mate and make it again at a new ratio, Flip False, under its old name."""
    if not delete_mate(asm, name):
        return None
    a = call(asm, "GetComponentByName", first_component)
    b = call(asm, "GetComponentByName", second_component)
    if not (select_feature_of(asm, a, "Gear Axis", False) and select_feature_of(asm, b, "Gear Axis", True)):
        return None
    mate, status, made = add_mate(asm, GEAR, CLOSEST, flip=False, ratio=(z_first, z_second))
    if mate is None or len(made) != 1:
        return None
    feature = mate_feature(asm, made[0])
    feature.Name = name                                   # read it back: SolidWorks renames on collision
    return str(call(feature, "Name"))
```

`delete_mate` is the deletion of [assemblies/02](02-mates-from-code.md#deleting-a-mate);
`GetComponentByName(name)` on **IAssemblyDoc** found each component by its
`Name2`.

## What each change did

| Change | What happened (2026 and 2024) |
|---|---|
| **Re-phase a gear**: `Transform2` put turning the output gear with its gear mate **on** | The put was kept; nothing else moved; the train then turned at its ratio from the new phase. No mate error. |
| The same put with the gear mate suppressed around it, then unsuppressed | Also kept. |
| A put on a gear that carries **two** gear mates (locks suppressed) | Held to 1e-6; nothing else turned; no mate error. |
| **Move a shaft**: the skeleton part's two globals for the output shaft changed (opened by path, activated, rebuilt there), then the assembly rebuilt | The output gear went with its axis, nothing else moved, no mate error, the ratio unchanged. **But the gear turned the wrong way as it went**: −(1 + z_partner/z_gear)·Δφ for a swing Δφ round the middle shaft, the opposite of the +(1 + z_partner/z_gear)·Δφ that keeps the pair in mesh. Put each gear back to the phase it should have after any shaft move. |
| **Move a gear along its shaft**: its axial distance mate's `D1` linked to an assembly global, the global changed | That gear moved along its shaft alone. |
| **Change a compound gear's angle and position**: the lock suppressed, the second gear put 11° round (and, separately, 3 mm along its axis and 11° round), the lock unsuppressed | The lock **re-took** the new relative frame: 11° and 3 mm kept after the lock came back and through a drive, on a +Z and a −Z middle shaft, no mate error. (A lock that ignored the put would have read a different angle after the drive.) |
| A put on a locked gear **with the lock on** | The put was kept, its locked partner **did not follow**, and no mate reported an error after the rebuild. **Then driven**, the two gears turned together by the same angle and their relative angle stayed where the put had left it: the lock took the new relation as its own, silently. |
| **New ratio by definition** (the recipe above) | 2026: `ModifyDefinition` returned `True`, the output turned at the new ratio, and the copy saved, closed, reopened, turned at the new ratio again, was set back and closed. **2024: the same ratio change worked, but the assembly could not be closed** — see below. |
| **New ratio by remake** | Right ratio and sense; saved, closed, reopened, right again, closed. The remade mate moved to the **end** of the `MateGroup` (8th of 20 before, last after) and was found by its name all the same. |
| The remake on a gear that carries **two** gear mates (locks suppressed) | The remade mate and the other gear mate were each found by name, and the joined trains turned at the new ratio through both. |

### A whole tooth-count change, in place

The remake was then run in the shape a tool needs for a tooth-count change, on
a two-stage train of **real gear parts** (a tool built the parts and the
skeleton; the mates were made as in
[assemblies/10](10-mate-a-gear-train-that-turns.md)): both gears of one stage
given new tooth counts with the same centre distance, by changing each part's
own globals in its own document; every lock suppressed; that stage's gear mate
deleted, made again at the new counts and given its old name; every gear put to
its new phase; the locks back on; one `ForceRebuild3(True)`. Then the mate
check was clean (every `AddMate5` status 1, no mate error), every gear stood at
its frame to 1e-6, a drive turned the output at the new overall ratio the same
way, every gear came back to its frame, interference at the new phase was 0,
and a full rebuild afterwards moved nothing.

- **Closed without saving and reopened**, the assembly was exactly as saved
  before: the old counts, the old gear mate definitions, the same frames.
- **Saved and reopened**, it had the new counts and ratio, the frames, a clean
  check and no interference.
- The same on a single-stage train with an **idler** (three gears, two gear
  mates on the idler): both of the idler's gear mates were deleted and made
  again; every gear stood at its new frame to 8e-15; driven, every gear turned
  as the new counts say.

**The interference check needs a control.** In the two-stage train the gears
clashed at their old phases (4 interferences) and were clean after the put; but
in the idler train the old phases happened to clear too (0). With one gear put
**half a tooth pitch** off its new phase, both trains clashed (4 and 6
interferences). So "no interference after the change" proves nothing unless the
same check, half a pitch off, finds one
([assemblies/03](03-interference-detection.md)).

### With the components lightweight

`ISldWorks.OpenDoc6(path, 2, options, "", out, out)` with options
1 + 128 (`swOpenDocOptions_Silent` | `swOpenDocOptions_LoadLightweight`) left
every component **fully resolved** (`IComponent2.GetSuppression2` 2) on this
installation. Only with 64 added (`swOpenDocOptions_OverrideDefaultLoadLightweight`,
options 193) did every component read 1 (`swComponentLightweight`). Then, on
both versions, the SOLIDWORKS CAM add-in put up a **modal "SOLIDWORKS CAM
Error"** box ("SOLIDWORKS CAM data cannot be restored because loading of
lightweight parts has been detected…"), which blocked `OpenDoc6` until it was
closed; the probe's dialog watch closed it with `WM_CLOSE`.

Reading `GetSuppression2` on every gear at each step, on both versions:

| Step | Every gear read | What happened |
|---|---|---|
| A plain `OpenDoc6` (option 1 only) | 2, fully resolved | — |
| After the lightweight open (options 193) | **1, lightweight** | — |
| After `FeatureByName("Gear Axis")` found the axis on two of them | still 1 | — |
| The train's **first drive**, one step: every component's `Transform2` read, a global set to turn the input 30°, `ForceRebuild3(True)`, every `Transform2` read again | — | the output gear **read −24.17° where 2.5° is right**; the other gears and the other train in the same assembly read right |
| After that step | **2, fully resolved** | — |
| The remake, and the drive after it | 2 | right: status 1, no mate error, the train turned at the new ratio |

Which call in that step resolved the components (the transform reads, the
global, the rebuild) was not separated, so it is not known; and the wrong
reading may be a stale transform read while the gear was still lightweight
rather than a wrong solve. Either way the remake and the drive after it ran on
components that were already resolved: nothing was shown to work **while**
they were lightweight. **Read `IComponent2.GetSuppression2` on every component
and require 2 (`swComponentFullyResolved`) before reading transforms, driving
or changing a mated train.** Only 2 was ever seen for a resolved component
(`swComponentResolved`, 3, never came).

### Correcting a gear mate that turns the wrong way

A gear mate's sense can be wrong as made: for a pinion in a toothed ring gear no
`Flip` known in advance is right on both versions
([assemblies/10](10-mate-a-gear-train-that-turns.md#checking-a-gear-mates-sense-after-making-it)).
The check and the fix, as a probe round ran them on a tool-built train with a
toothed ring pair: read each gear mate back (or, as a fallback, add a temporary
drive and judge each mesh by the sign of its driven gear's turn, then set the
drive back and delete it, every frame returning to about 1e-10 mm); remake a
wrong one by deletion and `AddMate5` with the other `Flip`, under its old name.
On SolidWorks 2026 the ring pair's mate had turned the ring the wrong way and,
driven 10° off its built phase, the pair clashed in 5 places; remade, it turned
the right way and stayed clear. The remade train matched a right-first-time one
to 2.3e-10 mm (1.1e-10 on 2024, where nothing needed remaking), with the same
mates once the remade one was counted last, no mate error, and only the
assembly marked modified.

A follow-up round showed that the read can come first: reading every gear
mate's sense marks no document, so a change can check the existing mates
before it touches anything. The remake also worked with `CommandInProgress`
True and no rebuild between making, reading, deleting and making again (wrong
to right shown on 2026 only; on 2024 the remake under it only went from right
to wrong). And after a remake at a new ratio, the new mate must be read back
too: on 2026 a ring mesh remade with `Flip` False read wrong, was made again
with `Flip` True, and then read right and turned right with no clash; on 2024
it read right first time. The first "wrong" on 2026 was the read-back's word
alone: the train was driven only after the second remake.

The same check ran inside an application on a ring mesh after its pinion had
been moved along its shaft and its tooth counts changed: the gear mate was
deleted, made again at the new ratio, read back wrong, and made again with the
other `Flip`. It ended right on SolidWorks 2024 and 2026: a drive through the
ring at the new ratio turned it the right way, also after a save and reopen,
with an interference control beside it. "Read back wrong" there is the
application's own reading; what SolidWorks showed is the end state. Even on one
version, the `Flip` a ring mate needs can change between makes
([assemblies/10](10-mate-a-gear-train-that-turns.md#checking-a-gear-mates-sense-after-making-it)),
so read back every remade mate, never reuse the `Flip` the old one had.

### The ratio change that strands an assembly on 2024

On SolidWorks 2024, after `IFeature.ModifyDefinition` had changed a gear
mate's ratio, `ISldWorks.CloseDoc` on that assembly **raised `0x80010105` ("The
server threw an exception")** and left it open; after that, further closes left
it open without a word, together with the skeleton part and gear part it uses,
until that SolidWorks was killed. It happened whether or not the assembly had
been saved first, in three 2024 runs, the last of them with that probe alone in
a session started for it. On 2026 the same code closed every copy. Use the
remake instead.

`IGearMateFeatureData` here has no `AccessSelections`: the call raised
`AttributeError` (`<unknown>.AccessSelections`) on both versions, and
`ModifyDefinition` worked without it. **Reading** a gear mate's definition
(`GetDefinition`, then `GearRatioNumerator` and `GearRatioDenominator`, no
`ModifyDefinition`) marked no document modified
([assemblies/12](12-rebuild-scope-and-the-save-flag.md#what-sets-getsaveflag)),
so a tool can check the ratios before deciding whether to change anything.

## Why it is not obvious

- **A placement is kept, not solved.** The re-phase works *because* a
  `Transform2` put does not drive the gear mate (§73): the mate takes the new
  phase as its starting point. The same fact means a put on a locked gear with
  the lock on silently changes the compound pair's relation for good: the lock
  holds the new angle from then on. Suppress every lock of the train around a
  put.
- **A moved shaft drags its gear round the wrong way**, with no error and the
  ratio still right: only the phase is wrong, and only a mesh or interference
  check shows it.
- **`ModifyDefinition` answers `True` and still costs you the session on
  2024.** Nothing before the close says anything is wrong.
- **Put the ratio in `AddMate5`'s order, not in the order you read it.** Putting
  the new count into the field that held the old one, alone or with the other
  field as read, made the inverse ratio (2026's first run).
- **A remade mate changes its place in the tree.** Find mates by name, not by
  position.

## What it does not do

- Trains only, not gear pairs with a centre-distance equation
  ([assemblies/02](02-mates-from-code.md)).
- A shaft move combined with a tooth change in one go was not run; each was
  run on its own.
- The CAM add-in's box is this installation's; with the add-in not loaded it
  would presumably not appear, which was not tried.

## Evidence

Gear-Generator probe tier 8, Python over pywin32 late binding.

- `motion_update`: SolidWorks 2026 34.0.0 (run 20261113-231301) and 34.1.1
  (20261114-034458, 20261114-081921), SolidWorks 2024 SP5 32.5.0
  (20261113-223412, a freshly started session). `layout_move_carries_mates = True`;
  `mesh_phase_route = "Transform2 put with the gear mate on"`;
  `put_with_gear_mate_on_moves = {'input': 0.0, 'output': <the put's angle>}`;
  `turn_on_a_shaft_move = {'as_a_multiple_of_the_need': -1.0, …}` (for a 20°
  swing, the gear's turn and the turn the mesh needed agreed to 1e-8 in size and
  were opposite in sign);
  `lock_unsuppress_keeps_the_new_angle = True` (relative angle 11.0 while
  suppressed, after unsuppressing and after the drive);
  `axial_global_moves_gear = True` (the other seven gears moved 0.0 mm);
  suppression by `"SetSuppression2 this configuration, None"` every time.
- The sense check and remake on a toothed ring pair: probe `ring_mate_sense`,
  SolidWorks 2026 34.1.1 (run 20261114-133014) and 2024 SP5 (run
  20261114-135104), fresh sessions: tooth clashes in the wrong-sense case were
  5 with the mate as first made and 0 after the remake on 2026, and 0 and 0 on
  2024; `ring_check_and_remake_holds = True` on both.
- The read before a change and the remake under `CommandInProgress` or at a new
  ratio: probe `ring_trains_saved`, SolidWorks 2024 SP5 (run 20261114-151013)
  and 2026 34.1.1 (run 20261114-162034), fresh sessions, 3 trains and 13 gear
  mates: no save flag changed across the reads; the remade mate's read under
  `CommandInProgress` equalled its read after the rebuild; the ratio remake
  read and turned right on both after the steps above.
- The read-back and remake after a pinion move and a tooth change: a
  whole-application run of 2026-11-14 on SolidWorks 2024 SP5 (32.5.0) and 2026
  34.1.1, fresh sessions; the end state shown by a drive through the ring at the
  new ratio, before and after a save and reopen, and an interference control.
- `gear_mate_ratio` (the remake), `gear_mate_update`, `lock_retake_offset`,
  `put_on_twice_meshed_gear`: SolidWorks 2026 34.1.1, full run 20261114-081921
  (85 of 85); SolidWorks 2024 SP5, run 20261114-071324 (47 of 47) in a session
  started fresh for it. `gear_mate_ratio_route = "remake"`, closed
  `{'closed': True, 'left': []}`, `remade_mate_position = {'before': 7, 'after': 19, 'count': 20}`
  (0-based); `lock_offset_kept = {'all Z+': True, 'middle Z-': True}` with
  `after_drive = {'along': 3.0, 'angle': 11.0, 'axis_off': 0.0, 'off_axis': 0.0}`;
  `put_on_twice_meshed_gear_holds = True`; `lock_on_put_turns` 7.0° for the put
  gear and 0.0 for its partner, then `lock_on_put_after_drive = {'anchor_turned': -2.5, 'follower_turned': -2.5, 'relative_angle_change': 0.0, 'errors': {}}`;
  `remake_on_twice_meshed_gear_holds = True`.
- `gear_mate_update` again with the half-pitch control, and `idler_update`,
  `lightweight_remake`: SolidWorks 2026 34.1.1, run 20261114-095421 (49 of 49),
  and SolidWorks 2024 SP5, run 20261114-102300 (49 of 49), each in a session
  started fresh. Interference counts, both versions: two-stage train
  `interference_before_put` 4, `interference_half_pitch` 4, after the put 0;
  idler train 0, 6 and 0. `lightweight_remake` (first form): options 129 left
  `swComponentFullyResolved`, options 193 gave `swComponentLightweight` on all
  eight, the CAM error box logged and closed.
- `lightweight_remake` with the state read at every step: SolidWorks 2026
  34.1.1, run 20261114-105135, and SolidWorks 2024 SP5, run 20261114-111150
  (34 of 34 each, fresh sessions). `states`: `after the open` and
  `after FeatureByName('Gear Axis')` all `[1, 'swComponentLightweight']`;
  `after the first drive`, `after the remake` and `after the drive that follows`
  all `[2, 'swComponentFullyResolved']`; `lightweight_first_drive_right = False`
  (`turns_before` read the output at −24.166666658° where 2.5° is right);
  `component_resolved_read = {'call': 'IComponent2.GetSuppression2', 'fully_resolved': 2, 'plain_open_values': [2]}`;
  the remade mate status 1 and the output at the new ratio.
- The definition route (`gear_mate_definition`, run last and never chosen):
  SolidWorks 2026 34.1.1 (20261114-081921) `definition_closes = {'both fields, the other way round': True}`;
  SolidWorks 2024 runs 20261114-040636, 20261114-051023 and 20261114-073328 (that
  probe alone, in a fresh session): the close `{'closed': False, 'raised': '0x80010105 — The server threw an exception.'}`.
  Both versions: `definition_numerator_is_second_teeth = True`; `AccessSelections`
  raised `AttributeError`.

- The listings (all but the definition route), on plain cylinders: the gear-train runner ([`code/python/gear_train/`](../../code/python/gear_train/README.md)), results `gear-train-check-20261114-140356` (SolidWorks 2026 34.1.1) and `gear-train-check-20261114-140631` (2024 SP5 32.5.0), 25 of 25 steps each. Both
  versions: `set_suppressed` both ways `True`; the re-phasing put kept 7.0° with
  the other gears at 0.0°, and a drive then turned the train at its ratio; the
  put on a locked gear turned it 5.0° and its partner 0.0°; the remake kept its
  name, moved from 9th of 10 to last, read back `[60.0, 20.0]`, and the train
  then turned at the new ratio.

The result files are kept in the Gear-Generator repository, not here.

## See also

- [assemblies/10 — Mate a gear train that turns](10-mate-a-gear-train-that-turns.md) — how the train was made
- [assemblies/02 — Mates from code](02-mates-from-code.md) — deleting, renaming and finding mates
- [assemblies/04 — Mates between non-parallel axes](04-mates-between-non-parallel-axes.md) — the `Transform2` put
- [assemblies/05 — Test motion with the drag operator](05-test-motion-with-the-drag-operator.md) — §73, placement versus motion
- [assemblies/12 — Rebuild an assembly without marking every part modified](12-rebuild-scope-and-the-save-flag.md)
- [documents/02 — Save as, and close](../documents/02-save-as-and-close.md) — closing, and the closes that did not work
- [features/09 — Twisted sweep](../features/09-twisted-sweep.md) — `ModifyDefinition` on other feature data
- [reading/12 — Snapshot suppression before you suppress](../reading/12-snapshot-suppression-before-you-suppress.md)
- [GOTCHAS §73, §96, §97, §98, §102, §104, §105](../../GOTCHAS.md)
- [assemblies/03 — Interference detection](03-interference-detection.md) — the check, and why it needs a half-pitch control
