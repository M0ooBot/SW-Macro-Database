---
id: assemblies-02-mates-from-code
title: Add coincident, distance and angle mates
status: verified
verified_on: SolidWorks 2026 (revisions 34.0.0 and 34.1.1); failing mates, deleting and renaming also on SolidWorks 2024 SP5 (32.5.0)
language: [python]
api: [IAssemblyDoc.AddMate5, IComponent2.FeatureByName, IFeature.Select2, IModelDocExtension.SelectByID2, IFeature.GetFirstSubFeature, IFeature.GetNextSubFeature, IEquationMgr.Add2, IFeature.GetErrorCode2, IComponent2.GetConstrainedStatus, IModelDocExtension.GetWhatsWrongCount, IModelDocExtension.GetWhatsWrong, IModelDoc2.EditDelete, IFeature.Name, IModelDoc2.FeatureByName]
keywords: [AddMate5, mate, coincident mate, distance mate, angle mate, swMateType_e, swMateCOINCIDENT, swMateDISTANCE, swMateANGLE, swMateAlign_e, MateGroup, MateCoincident, MateDistanceDim, MatePlanarAngleDim, FeatureByName, selection mark 1, drive mate from global, mate refused, AddMate5 status 0, AddMate5 status 5, over-defined assembly, swAddMateError_OverDefinedAssembly, GetErrorCode2 46, GetErrorCode2 47, GetErrorCode2 51, IsWarning, GetWhatsWrong, GetConstrainedStatus 4, delete a mate, EditDelete, DeleteSelection2, rename a mate, find a mate by name, suppressed mate error code 0, unsuppress marks modified]
answers: "How do I add coincident, distance and angle mates between assembly components from code?"
---

# Add coincident, distance and angle mates

## What this is for

Components inserted into an assembly
([assemblies/01](01-new-assembly-and-insert-components.md)) float. Mates put
them where they belong, and a distance or angle mate carries a dimension that a
global can drive, so a centre distance becomes an equation. This entry is how
to select what to mate, the `AddMate5` call that ran, how to find the mate it
made, and how to link its dimension.

## Selecting a component's plane or axis

Select the two entities at selection mark **1**. The probe's route: ask the
component for the feature by name, select it, and fall back to
`SelectByID2` with the assembly-qualified name.

```python
def _select_in_component(px: Px, asm: Any, component: Any, feature_name: str, kind: str,
                         append: bool, mark: int = 1) -> bool:
    """A component's plane or axis: FeatureByName then Select2, else SelectByID2 by full name."""
    before = sc.selected_count(asm)
    if not append:
        call(asm, "ClearSelection2", True)
        before = 0
    feature = call(component, "FeatureByName", feature_name)
    if feature is not None and sc._retrying(asm, lambda: call(feature, "Select2", append, mark), before,
                                            "component FeatureByName.Select2"):
        return True
    asm_name = os.path.splitext(str(call(asm, "GetTitle")))[0]
    full = f"{feature_name}@{call(component, 'Name2')}@{asm_name}"
    if call(sc.extension(asm), "SelectByID2", full, kind, 0.0, 0.0, 0.0, append, mark, sc.null(), 0) and \
            sc.selected_count(asm) > before:
        sc._count(f"SelectByID2 {kind} in component")
        return True
    return False
```

`FeatureByName` is on **IComponent2**; `Select2(append, mark)` on **IFeature**;
`SelectByID2` on **IModelDocExtension**. `sc._retrying` repeats the select up to
four times and counts it only if `GetSelectedObjectCount2` went up. The plane
names passed in were read from the part's tree in order (Front, Top, Right),
not typed. **Which of the two routes made each selection was not recorded**;
every selection succeeded.

## The call

```python
# swMateType_e, swMateAlign_e, swAddMateError_e, from swconst.tlb on SolidWorks 2026.
MATE_COINCIDENT = 0
MATE_DISTANCE = 5
MATE_ANGLE = 6
ALIGN_CLOSEST = 2

def _mate(px: Px, asm: Any, label: str, kind: int, distance: float = 0.0, angle: float = 0.0) -> Optional[str]:
    before = [n for n, _ in _mate_features(asm)]
    got, result = px.attempt(
        f"AddMate5 {label}",
        lambda: call(asm, "AddMate5", kind, ALIGN_CLOSEST, False, distance, distance, distance, 1, 1,
                     angle, angle, angle, False, False, 0, sc.out_long()),
    )
    call(asm, "ClearSelection2", True)
    mate, status = (result[0], result[1]) if got and isinstance(result, tuple) else (result, None)
    px.fact(f"mate {label}", {"returned": type(mate).__name__ if got else "raised", "status": status})
    made = [n for n, _ in _mate_features(asm) if n not in before]
    if not px.check(got and mate is not None and len(made) == 1, f"{label}: one mate appears under Mates"):
        return None
    return made[0]
```

`AddMate5` is on **IAssemblyDoc**. The fifteen arguments as they ran: type,
alignment `2`, `False`, the distance three times in **metres**, `1`, `1`, the
angle three times in **radians**, `False`, `False`, `0`, and a by-reference
long. Nothing else was varied here. The third argument, `Flip`, was later set
`True` on a point-to-plane distance mate, where it put the point on the plane's
negative side ([assemblies/04](04-mates-between-non-parallel-axes.md)).

**Finding the mate it made** — mates live under the `MateGroup` feature as
sub-features:

```python
def _mate_features(asm: Any) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for feature in sc.top_features(asm):
        if sc.type_name(feature) == "MateGroup":
            child = call(feature, "GetFirstSubFeature")
            while child is not None:
                out.append((str(call(child, "Name")), sc.type_name(child)))
                child = call(child, "GetNextSubFeature")
    return out
```

The four mates of a gear pair, in the order they were added:

```python
px.require(_select_in_component(px, asm, second, front, "PLANE", False) and
           _select_in_component(px, asm, first, front, "PLANE", True), "the two front planes select")
_mate(px, asm, "coincident fronts", MATE_COINCIDENT)
px.require(_select_in_component(px, asm, second, "Gear Axis", "AXIS", False) and
           _select_in_component(px, asm, first, top, "PLANE", True), "B's axis and A's top plane select")
_mate(px, asm, "axis on top plane", MATE_COINCIDENT)
px.require(_select_in_component(px, asm, second, "Gear Axis", "AXIS", False) and
           _select_in_component(px, asm, first, right, "PLANE", True), "B's axis and A's right plane select")
distance = _mate(px, asm, "distance axis to right plane", MATE_DISTANCE, distance=CENTRE / sc.MM)
px.require(_select_in_component(px, asm, second, top, "PLANE", False) and
           _select_in_component(px, asm, first, top, "PLANE", True), "the two top planes select")
angle = _mate(px, asm, "angle between top planes", MATE_ANGLE, angle=math.radians(3.0))
```

**Driving the distance from a global** — rename the mate, find its dimension by
value ([features/04](../features/04-read-a-features-dimensions.md)), link it
([equations/02](../equations/02-link-a-dimension-to-a-global.md)):

```python
feature.Name = "Centre Distance"
px.check(str(call(feature, "Name")) == "Centre Distance", "the distance mate renames and reads back")
dims = sc.dimensions_of(feature)
values = [(str(call(d, "Name")), float(call(d, "SystemValue"))) for d in dims]
px.fact("distance_mate_dimensions", values)
if with_link:
    match = [d for d in dims if abs(float(call(d, "SystemValue")) - CENTRE / sc.MM) < 1e-9]
    px.require(len(match) == 1, "the distance mate's dimension is found by value")
    dim_name = str(call(match[0], "Name"))
    eqm = call(asm, "GetEquationMgr")
    add = adder(px, eqm)
    index = add('"Centre Distance"= 60')
    px.require(index >= 0, "an assembly global is added")
    link = add(f'"{dim_name}@Centre Distance"= "Centre Distance"')
    px.require(link >= 0, f'the link "{dim_name}@Centre Distance"= "Centre Distance" is accepted')
    sc.put_indexed(eqm, "Equation", index, '"Centre Distance"= 70')
    call(asm, "ForceRebuild3", False)
```

## The tool's form, and an angle mate linked to a global

After the probe, the same call went into the tool that builds a gear pair's
assembly:

```python
def add_mate(self, handle: str, kind: str, a: str, b: str, value: float = 0.0, name: str = "") -> Tuple[str, str]:
    """``AddMate5`` on two component references; returns ``(mate name, its dimension)``.

    Probe assembly_components_and_mates: coincident, distance and angle
    mates were made this way and the component moved to where they said.
    """
    types = {"coincident": findings.MATE_COINCIDENT, "distance": findings.MATE_DISTANCE,
             "angle": findings.MATE_ANGLE}
    if kind not in types:
        raise SolidWorksError(f"There is no verified mate type for {kind!r}.")
    before = self._mate_names()
    self._component_ref(a, append=False)
    self._component_ref(b, append=True)
    distance = value / MM_PER_METRE if kind == "distance" else 0.0
    angle = math.radians(value) if kind == "angle" else 0.0
    mate = call(self._doc(), "AddMate5", types[kind], findings.MATE_ALIGN_CLOSEST, False, distance, distance,
                distance, 1, 1, angle, angle, angle, False, False, 0, _out_long())
    call(self._doc(), "ClearSelection2", True)
    made = [n for n in self._mate_names() if n not in before]
    if mate is None or len(made) != 1:
        raise SolidWorksError(f"AddMate5 would not make a {kind} mate between {a} and {b}.")
    feature = self._mate_feature(made[0])
    kept = self._rename(feature, name) if name else made[0]
    dim = ""
    if kind in ("distance", "angle"):
        wanted = distance if kind == "distance" else angle
        matches = [d for d in self._dimensions(feature) if abs(float(call(d, "SystemValue")) - wanted) < 1e-9]
        dim = str(call(matches[0], "Name")) if len(matches) == 1 else ""
    self._handles[handle] = {"mate": kept}
    return kept, dim
```

`_component_ref` makes the two selections at mark 1 as above; `_mate_names`
lists the `MateGroup` children; `_dimensions` is the display-dimension walk in
[features/04](../features/04-read-a-features-dimensions.md). The value is in
millimetres or degrees, converted to metres or radians at the call.

A pair built through the tool's window on SolidWorks 2026 (revision 34.0.0) made
four mates this way, two of them named and linked to assembly globals:

```
ok      mate coincident gear2:plane1 ~ gear1:plane1
ok      mate coincident gear2:Gear Axis ~ gear1:plane2
ok      mate distance gear2:Gear Axis ~ gear1:plane3 as Centre Distance
ok      link "D1@Centre Distance"
ok      mate angle gear2:plane2 ~ gear1:plane2 as Mesh Angle
ok      link "D1@Mesh Angle"
ok      3 globals read back and match the maths
ok      rebuilt once
```

Read back from the assembly afterwards:

- Equations, in order: `"Centre Distance"= 60`, `"Ratio"= 3`,
  `"Mesh Angle"= 3`, `"D1@Centre Distance"= "Centre Distance"`,
  `"D1@Mesh Angle"= "Mesh Angle"`.
- **The angle mate's dimension** was `[('D1', 0.05235987755983)]`, 3° in
  radians, and its link to the global was accepted and read back. That is all
  that was observed: the angle global was not changed afterwards, so whether the
  angle follows it is not known.
- The distance mate's dimension was `[('D1', 0.06)]`. The components sat at
  (-0.0012, -0.0001, -5.0001) mm and (59.9988, -0.0001, -5.0001) mm (translations
  rounded to 0.0001 mm). With `"Centre Distance"` changed to 61 by an indexed put
  of `Equation(i)` and one `ForceRebuild3` (which returned `True`), the dimension
  read 0.061 and the second component moved to x = 60.9988 mm while the first
  stayed put: 61 mm apart, the same small offset on both.

## When a mate is refused or over-defines

Added from the Gear-Generator probe's tier 8 (`p8_motion.py`, `add_mate` as
quoted in [assemblies/10](10-mate-a-gear-train-that-turns.md#the-calls)), on
SolidWorks 2026 (34.0.0, 34.1.1) and 2024 SP5 (32.5.0). The status out
parameter was read from the by-reference long's `.value` after the call (the
call itself still returned the mate alone):

- **Refused:** `AddMate5` returned `None`, no mate appeared under `MateGroup`,
  and the status read **0** (`swAddMateError_ErrorUknown`). Seen for a
  concentric mate between two reference axes, and for a gear mate between two
  reference axes that both belong to one component (the skeleton part's
  shaft axes) ([assemblies/10](10-mate-a-gear-train-that-turns.md)).
- **Solved:** status **1** (`swAddMateError_NoError`).
- **Over-defined:** a second angle mate 10° off an existing one between the same
  two planes. The status read **5** (`swAddMateError_OverDefinedAssembly`) **but
  the mate was made**, and `ForceRebuild3` still returned `True`.

How the over-definition showed, read like this (copied from [`code/python/gear_train/gear_train_check.py`](../../code/python/gear_train/gear_train_check.py); it ran on SolidWorks 2026 (34.1.1) and 2024 SP5 (32.5.0), results `gear-train-check-20261114-140356` and `gear-train-check-20261114-140631` beside it):

```python
import pythoncom
from win32com.client import VARIANT


def call(obj, name, *args):
    """Late-bound member: invoked when given arguments, read by attribute access otherwise."""
    member = getattr(obj, name)
    return member(*args) if args else member


def error_code(feature):
    """IFeature.GetErrorCode2: (code, is only a warning), with the warning flag as a by-reference bool."""
    flag = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, False)
    result = call(feature, "GetErrorCode2", flag)
    if isinstance(result, tuple):                  # pywin32 may hand the out value back in a tuple
        return result[0], (result[1] if len(result) > 1 else None)
    return result, flag.value
```

```python
def whats_wrong(asm):
    """IModelDocExtension.GetWhatsWrongCount, and GetWhatsWrong with its three out parameters."""
    ext = call(asm, "Extension")
    count = call(ext, "GetWhatsWrongCount")
    # Its three arrays are out parameters: with none passed it raised "Parameter not optional".
    outs = [VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT, None) for _ in range(3)]
    returned = call(ext, "GetWhatsWrong", *outs)
    listed = returned if isinstance(returned, tuple) else (returned,) + tuple(o.value for o in outs)
    features = [str(call(item, "Name")) for item in (listed[1] or ())]
    return {"count": count, "returned": listed[0], "features": features,
            "codes": listed[2], "warnings": listed[3]}
```

`GetErrorCode2` is on **IFeature** (the mate's sub-feature), `GetWhatsWrongCount`
and `GetWhatsWrong` on **IModelDocExtension**, `GetConstrainedStatus` on
**IComponent2** (read by attribute access, and called only if a method came
back, as in [assemblies/10](10-mate-a-gear-train-that-turns.md#one-degree-of-freedom-and-a-drive)).

| Reading | SolidWorks 2026 | SolidWorks 2024 |
|---|---|---|
| The new, conflicting mate's `GetErrorCode2` | **47** (`swFeatureErrorMateIlldefined`), warning `False` | **51**, warning `False` |
| The mates it fights | **46** (`swFeatureErrorMateOverdefined`), warning `True` | **51**, warning `True` |
| The over-defined component's `GetConstrainedStatus` | **4** (its partner 3) | **4** |
| `GetWhatsWrongCount` | rose from 6 to 8; `GetWhatsWrong` named the mates, with their codes and warning flags | 8, every code 51 |
| `ForceRebuild3` | `True` | `True` |

The same mates were flagged with the same warning flags on both versions; only
the numbers differ. 51 is the number `swconst` names
`swSketchErrorExtRefFail`, which says nothing about mates. So: check the
status, treat **any non-zero `GetErrorCode2`** on a mate as a problem, take the
mate whose warning flag is `False` as the one at fault, and never read meaning
into the number. On 2026 a mate also read code **1** with the warning flag
`True` in an over-defined group. `GetWhatsWrong` needs its three by-reference
out parameters; called with none it raised "Parameter not optional".

## Deleting a mate

```python
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
```

The probe kept `IModelDocExtension.DeleteSelection2(0)` as a fallback behind
this. `IFeature.Select2(False, 0)` on the mate then `IModelDoc2.EditDelete()`
with parentheses deleted it every time, on both versions (the over-defining mate,
drive mates, gear mates being remade); `DeleteSelection2` was never reached.
After deleting the over-defining mate its errors went and the component read
`GetConstrainedStatus` 3 again. `EditDelete` reached by attribute access
without parentheses is only fetched, as with `FixComponent`
([GOTCHAS §31](../../GOTCHAS.md)): an early run of this probe did exactly that.

## Renaming a mate and finding it again

```python
def rename(feature, name):
    """An IFeature.Name put, read back: SolidWorks renames quietly on a collision."""
    feature.Name = name
    return str(call(feature, "Name"))
```

A lock, a gear mate, an axis (coincident) mate, an axial distance mate and a
suppressed lock in a gear train were renamed by an `IFeature.Name` put (to
names such as `GearC locked to GearB` and `GearC meshes GearD`): each read its
new name back; nothing moved, and no mate's type, suppression or error code
changed. Saved, closed and reopened, each was found by its new name both by the
`MateGroup` walk and by `IModelDoc2.FeatureByName`; no old name was left; each
was still its kind (`IMate2.Type` 16, 10, 0, 5, 16; the lock's type name is
`MateLock`), the suppressed lock still suppressed; and driven, the train turned
as before ([assemblies/10](10-mate-a-gear-train-that-turns.md)). SolidWorks
2026 (34.1.1) and 2024 (32.5.0), each in a session started fresh.

**Renaming straight after `AddMate5` also works.** In a new, unsaved assembly,
each of a train's 18 mates renamed by an `IFeature.Name` put right after its
`AddMate5` (with `CommandInProgress` on) read its new name back at once and was
found by it; saved and reopened, every mate was found by its new name and no
first name was left. A mate that is deleted and made again goes to the end of
the `MateGroup` ([assemblies/11](11-change-a-mated-gear-train.md#what-each-change-did)),
so find mates by name, never by position.

## Suppressed mates read clean

A suppressed mate's `GetErrorCode2` read **0** with the warning flag `False`,
whether it was a sound lock or the conflicting angle mate that over-defined the
assembly when it was on. So a mate check that reads only error codes passes a
suppressed conflict: read `IsSuppressed2` too. And `SetSuppression2(1, 1, None)`
on a mate that is already on returned `True`, changed nothing, raised no error,
and still **marked the assembly modified**: `GetSaveFlag` read straight before
and straight after the call, nothing in between, went from `False` to `True` for
the assembly alone
([assemblies/12](12-rebuild-scope-and-the-save-flag.md#what-sets-getsaveflag)).
SolidWorks 2026 (34.1.1) and 2024 SP5, fresh sessions (the pinned reading in
runs 20261114-105135 and 20261114-111150).

## An angle mate following its global

Later observed in [assemblies/10](10-mate-a-gear-train-that-turns.md#one-degree-of-freedom-and-a-drive):
an angle mate between two planes, its `D1` linked to an assembly global, turned
its component by exactly the change in the global (90° → 120° turned it +30°;
back to 90° put it back), on SolidWorks 2026 and 2024.

## Why it is not obvious

**It returned the mate, not a tuple.** With a by-reference long for the error
code, pywin32 might be expected to return `(mate, error)`. Each of the four
calls returned the mate object alone, so the error out value was never seen.
Check the result for `None` and diff the `MateGroup` children: each call added
exactly one.

**Type names in the tree differ from the enum names.** The four mates read
`Coincident1` and `Coincident2` (`MateCoincident`), the distance
(`MateDistanceDim`), and `Angle1` (`MatePlanarAngleDim`).

**A mate's dimension is `D1`, and it is live.** The distance mate's only
dimension was `('D1', 0.06)`. Linked as `"D1@Centre Distance"` to an assembly
global, changing the global from 60 to 70 and rebuilding moved component B
from 60 mm to 70 mm.

## What it does not do

- Alignment values other than `2`, and every argument other than type,
  distance and angle, were not varied.
- The effect of the 3° angle mate on B's orientation was not measured; only
  that the mate was created.
- No failing mate was produced in the runs this entry first came from. Since
  then, see [When a mate is refused or over-defines](#when-a-mate-is-refused-or-over-defines):
  `None` with status 0 for a refused mate, the mate with status 5 for an
  over-defining one.
- Which selection route (`FeatureByName` plus `Select2`, or `SelectByID2`)
  succeeded is not recorded.
- An angle mate's dimension linked to a global was accepted and read back, but
  the global was never changed afterwards in these runs. It has since been
  observed following its global ([above](#an-angle-mate-following-its-global)).

## Evidence

SolidWorks 2026 (revision 34.0.0), Python over pywin32, probe run
20260914-180426, probes `assembly_components_and_mates` and
`assembly_distance_link` in
[`code/python/gear_generator/probe/p4_assembly.py`](../../code/python/gear_generator/probe/p4_assembly.py).

- Each of the four `AddMate5` calls: `{'returned': 'CDispatch', 'status': None}`,
  and one new mate under `MateGroup`.
- `mates = [('Coincident1', 'MateCoincident'), ('Coincident2', 'MateCoincident'), ('Centre Distance', 'MateDistanceDim'), ('Angle1', 'MatePlanarAngleDim')]`.
- After `ForceRebuild3`, `component_b_translation_mm_mated = (60.0, 0.0, -5.0)`,
  60 mm from A's axis.
- `distance_mate_dimensions = [('D1', 0.06)]`.
- `assembly_distance_link`: the link `"D1@Centre Distance"= "Centre Distance"`
  accepted; `component_b_translation_mm_after_global_70 = (70.0, 0.0, -5.0)`.
- A later gear pair built by the tool on the same session: the angle-mate link
  accepted, and the centre distance moved 60 → 61 mm, as described above. That
  run's output is quoted in this entry; its log is not kept in this repo.
- Renaming at once, suppressed mates: probe `mates_under_command_in_progress`,
  SolidWorks 2026 34.1.1 (run 20261114-095421) and 2024 SP5 (run
  20261114-102300): `mate_rename_at_once_holds = True`;
  `suppressed_mate_error_codes = {'sound': {'type': 'MateLock', 'code': 0, 'warning': False, 'suppressed': True}, 'conflicting': {'type': 'MatePlanarAngleDim', 'code': 0, 'warning': False, 'suppressed': True}}`.
- Failing mates, deleting and renaming: Gear-Generator probe tier 8, probes
  `shaft_axis_mates`, `gear_mate_sense`, `compound_lock` and `lock_mate_rename`,
  on SolidWorks 2026 34.0.0 (run 20261113-231301) and 34.1.1 (20261114-034458),
  and SolidWorks 2024 SP5 32.5.0 (20261113-223412; `lock_mate_rename` in
  20261114-071324, a fresh session). `compound_lock`'s `over_defined`:
  `mate = {'returned': 'CDispatch', 'status': 5, 'status_name': 'swAddMateError_OverDefinedAssembly'}`,
  `rebuild = {'returned': True}`, `constrained = {'p': 3, 'q': 4}`,
  `whats_wrong.count` 8 (6 before), `deleted_by = 'Select2 then EditDelete()'`,
  `constrained_after_delete = {'p': 3, 'q': 3}`; the codes as in the table.
  `lock_mate_rename`: `mate_rename_route = 'IFeature.Name put'`,
  `mate_find_routes = {'FeatureByName': True, 'mate group': True}`,
  `moved_by_the_rename 0.0`. Those result files are kept in the Gear-Generator
  repository, not here.
- The over-definition, deletion and renaming listings, again, by the gear-train runner ([`code/python/gear_train/`](../../code/python/gear_train/README.md)), results `gear-train-check-20261114-140356` (SolidWorks 2026 34.1.1) and `gear-train-check-20261114-140631` (2024 SP5 32.5.0): status 5
  with the mate made; codes 47 / 46 on 2026 and 51 for each on 2024; the
  over-defined component 4, then 3 after the deletion; the suppressed conflict
  `[0, False]`; every mate renamed straight after its `AddMate5` and found by
  the new name after a reopen.

## See also

- [assemblies/01 — New assembly and insert components](01-new-assembly-and-insert-components.md)
- [equations/02 — Link a dimension to a global](../equations/02-link-a-dimension-to-a-global.md)
- [features/04 — Read a feature's dimensions](../features/04-read-a-features-dimensions.md)
- [equations/01 — Global variables from code](../equations/01-global-variables-from-code.md) — the indexed put that changed the global
- [reading/04 — Read the selection](../reading/04-read-the-selection.md)
- [connect/08 — Find a feature by name](../connect/08-find-a-feature-by-name.md) — sub-features
- [assemblies/03 — Interference detection](03-interference-detection.md) — whether mated parts collide
- [assemblies/04 — Mates between non-parallel axes](04-mates-between-non-parallel-axes.md) — origins, angles between axes, and `Flip`
- [assemblies/05 — Test motion with the drag operator](05-test-motion-with-the-drag-operator.md) — whether the mated parts can move, and which mate stops them
- [assemblies/06 — Read every mate](06-read-every-mate.md) — reading back mates someone else made
- [assemblies/07 — Configurations that hold different positions](07-configurations-that-hold-different-positions.md) — mates that pin one position per configuration
- [assemblies/10 — Mate a gear train that turns](10-mate-a-gear-train-that-turns.md) — gear mates, lock mates, and the axis mate that is refused
- [assemblies/11 — Change a mated gear train](11-change-a-mated-gear-train.md) — suppressing, deleting and remaking mates in a train
- [GOTCHAS §31, §83, §94, §95, §103](../../GOTCHAS.md)
