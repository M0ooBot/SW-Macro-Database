---
id: assemblies-11-change-a-mated-gear-train
title: Change a mated gear train in place — re-phase a gear, move a shaft, re-take a lock, change a gear mate's ratio
status: partly-verified
verified_on: SolidWorks 2026 (revisions 34.0.0 and 34.1.1) for all of it; SolidWorks 2024 SP5 (32.5.0) for the phase, shaft-move and suppressed-lock changes in a clean session, and for the rest only in a session holding an assembly it could not close
language: [python]
api: [IComponent2.Transform2, IFeature.SetSuppression2, IFeature.IsSuppressed2, IFeature.GetDefinition, IFeature.ModifyDefinition, IGearMateFeatureData.GearRatioNumerator, IGearMateFeatureData.GearRatioDenominator, IModelDoc2.EditDelete, IAssemblyDoc.GetComponentByName, IAssemblyDoc.AddMate5, ISldWorks.CloseDoc]
keywords: [change gear ratio, gear mate ratio, ModifyDefinition gear mate, IGearMateFeatureData put, AccessSelections AttributeError, 0x80010105, server threw an exception, CloseDoc cannot close, assembly will not close, remake gear mate, delete and re-add mate, lock mate re-take, suppress lock, re-phase gear, mesh phase, Transform2 put with gear mate, lock does not hold against put, shaft moved by globals, skeleton part, axial distance global]
answers: "My gear train is mated and turns; how do I change it from code afterwards — turn one gear to a new phase, move a shaft, change a compound gear's angle or position, or give a gear mate a new ratio — without breaking the mates?"
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
late binding. `put(px, doc, component, matrix, origin)` is the `Transform2` put
of [assemblies/04](04-mates-between-non-parallel-axes.md) followed by a rebuild.

**Suppressing and unsuppressing one mate**, judged by reading the state back:

```python
def suppress(px: Px, asm: Any, name: str, on: bool) -> Optional[str]:
    """Suppress or unsuppress one mate; the route that did it, judged by ``IsSuppressed2``, or None."""
    enums = _enums(px)
    action = enums["suppress"] if on else enums["unsuppress"]
    feature = mate_feature(asm, name)

    def state() -> Optional[bool]:
        return is_suppressed(px, feature)

    routes: List[Tuple[str, Callable[[], Any]]] = [
        ("SetSuppression2 this configuration, None",
         lambda: call(feature, "SetSuppression2", action, enums["this_configuration"], None)),
        ("SetSuppression2 this configuration, null dispatch",
         lambda: call(feature, "SetSuppression2", action, enums["this_configuration"], sc.null())),
        ("Select2 then EditSuppress2()" if on else "Select2 then EditUnsuppress2()",
         lambda: (call(feature, "Select2", False, 0), getattr(asm, "EditSuppress2" if on else "EditUnsuppress2")())[1]),
    ]
    for label, thunk in routes:
        px.attempt(f"{label} on {name}", thunk)
        call(asm, "ClearSelection2", True)
        if state() is on:
            return label
    return None
```

`swFeatureSuppressionAction_e` `swSuppressFeature` 0 / `swUnSuppressFeature` 1
and `swInConfigurationOpts_e` `swThisConfiguration` 1, read from `swconst.tlb`.
`is_suppressed` reads `IFeature.IsSuppressed2(1, null)` (this configuration),
falling back to `IsSuppressed`. **The first route,
`IFeature.SetSuppression2(action, 1, None)`, did it every time**, for gear
mates, locks and angle mates, both ways, on both versions; the other two were
never needed.

**Changing a gear mate's ratio through its definition:**

```python
def set_gear_ratio_by_definition(px: Px, doc: Any, name: str, recipe: str, old: float, new: float,
                                 access: bool = True) -> Dict[str, Any]:
    """``GetDefinition`` of a gear mate, the fields ``recipe`` names put, ``ModifyDefinition(data, doc, None)`` (the
    pattern of TWIST_REVERSE_ROUTE, ``AccessSelections`` first when ``access``); what each step answered."""
    feature = mate_feature(doc, name)
    out: Dict[str, Any] = {"recipe": recipe, "before": gear_mate_definition(px, doc, name), "access_selections": access}
    got, data = px.attempt(f"GetDefinition of {name} to change it", lambda: call(feature, "GetDefinition"))
    if not got or data is None:
        out["definition"] = None
        return out
    if access:
        got, value = px.attempt(f"AccessSelections(doc, None) on {name}'s definition",
                                lambda: call(data, "AccessSelections", doc, sc.null()))
        out["accessed"] = plain(value) if got else "raised"
    fields = ratio_fields(recipe, out["before"], old, new)
    out["fields"] = fields
    if not fields:
        return out
    out["put"] = all(px.attempt(f"IGearMateFeatureData.{k} = {v:g}", lambda k=k, v=v: setattr(data, k, v))[0]
                     for k, v in fields.items())
    got, modified = px.attempt(f"ModifyDefinition(data, doc, None) of {name}",
                               lambda: call(feature, "ModifyDefinition", data, doc, sc.null()))
    out["modified"] = plain(modified) if got else "raised"
    if access and out.get("accessed") is True and not (got and modified):
        ok, value = px.attempt(f"ReleaseSelectionAccess on {name}'s definition",
                               lambda: member(data, "ReleaseSelectionAccess")[0])
        out["released"] = plain(value) if ok else "raised"
    out["after"] = gear_mate_definition(px, doc, name)
    return out
```

`ratio_fields` decides what to put. The recipe that gave the right ratio,
`"both fields, the other way round"`, puts the two counts **in `AddMate5`'s
order** (first selection's count in `GearRatioNumerator`), although
`GetDefinition` reads them back the other way round
([assemblies/10](10-mate-a-gear-train-that-turns.md#a-gear-mate)).

**Changing it by deleting the gear mate and making it again** ("remake"):

```python
def remake_gear_mate(px: Px, doc: Any, names: Mapping[str, str], name: str, first: str, second: str,
                     ratio: Tuple[float, float], new_name: str) -> Dict[str, Any]:
    """Delete a gear mate (MATE_DELETE_ROUTE) and make it again between the two components found by
    ``GetComponentByName``, at ``ratio`` with GEAR_MATE_FLIP, named ``new_name``; what happened."""
    enums = _enums(px)
    out: Dict[str, Any] = {"deleted_by": delete_mate(px, doc, name)}
    if not out["deleted_by"]:
        return out
    a, b = call(doc, "GetComponentByName", names[first]), call(doc, "GetComponentByName", names[second])
    picked = a is not None and b is not None and bool(select_in(px, doc, a, "Gear Axis", "AXIS", False)) and \
        bool(select_in(px, doc, b, "Gear Axis", "AXIS", True))
    out["selected"] = picked
    if not picked:
        return out
    out["made"] = add_mate(px, doc, f"{first}-{second} gear {ratio[0]:g}:{ratio[1]:g} made again", enums["gear"],
                           enums["closest"], flip=bool(findings.GEAR_MATE_FLIP), ratio=ratio)
    if out["made"]["name"]:
        out["name"] = _rename(px, mate_feature(doc, out["made"]["name"]), new_name)
        out["definition"] = gear_mate_definition(px, doc, out["name"])
    return out
```

`findings.GEAR_MATE_FLIP` is `False`. `delete_mate` is `IFeature.Select2(False, 0)`
then `IModelDoc2.EditDelete()` ([assemblies/02](02-mates-from-code.md#deleting-a-mate));
`_rename` is an `IFeature.Name` put read back; `GetComponentByName(name)` on
**IAssemblyDoc** found each component by its `Name2`.

## What each change did

| Change | What happened (2026 and 2024 unless said) |
|---|---|
| **Re-phase a gear**: `Transform2` put turning the output gear with its gear mate **on** | The put was kept; nothing else moved; the train then turned at its ratio from the new phase. No mate error. |
| The same put with the gear mate suppressed around it, then unsuppressed | Also kept. |
| A put on a gear that carries **two** gear mates (locks suppressed) | Held to 1e-6; nothing else turned; no mate error. |
| **Move a shaft**: the skeleton part's two globals for the output shaft changed (opened by path, activated, rebuilt there), then the assembly rebuilt | The output gear went with its axis, nothing else moved, no mate error, the ratio unchanged. **But the gear turned the wrong way as it went**: −(1 + z_partner/z_gear)·Δφ for a swing Δφ round the middle shaft, the opposite of the +(1 + z_partner/z_gear)·Δφ that keeps the pair in mesh. Put each gear back to the phase it should have after any shaft move. |
| **Move a gear along its shaft**: its axial distance mate's `D1` linked to an assembly global, the global changed | That gear moved along its shaft alone. |
| **Change a compound gear's angle and position**: the lock suppressed, the second gear put 11° round (and, separately, 3 mm along its axis and 11° round), the lock unsuppressed | The lock **re-took** the new relative frame: 11° and 3 mm kept after the lock came back and through a drive, on a +Z and a −Z middle shaft, no mate error. (A lock that ignored the put would have read a different angle after the drive.) |
| A put on a locked gear **with the lock on** | The put was kept, its locked partner **did not follow**, and no mate reported an error after the rebuild. What the lock does at its next solve was not measured. |
| **New ratio by definition** (the recipe above) | 2026: `ModifyDefinition` returned `True`, the output turned at the new ratio, and the copy saved, closed, reopened, turned at the new ratio again, was set back and closed. **2024: the same ratio change worked, but the assembly could not be closed** — see below. |
| **New ratio by remake** | Right ratio and sense; saved, closed, reopened, right again, closed — on both versions (2024 caveat below). |

### The ratio change that strands an assembly on 2024

On SolidWorks 2024, after `IFeature.ModifyDefinition` had changed a gear
mate's ratio, `ISldWorks.CloseDoc` on that assembly **raised `0x80010105` ("The
server threw an exception")** and left it open; after that, further closes left
it open without a word, together with the skeleton part and gear part it uses,
until that SolidWorks was killed. It happened whether or not the assembly had
been saved first, in both committed 2024 runs that tried it. On 2026 the same
code closed every copy.

`IGearMateFeatureData` here has no `AccessSelections`: the call raised
`AttributeError` (`<unknown>.AccessSelections`) on both versions, and
`ModifyDefinition` worked without it.

## Why it is not obvious

- **A placement is kept, not solved.** The re-phase works *because* a
  `Transform2` put does not drive the gear mate (§73): the mate takes the new
  phase as its starting point. The same fact means a put on a locked gear with
  the lock on breaks the compound pair silently. Suppress every lock of the
  train around a put.
- **A moved shaft drags its gear round the wrong way**, with no error and the
  ratio still right: only the phase is wrong, and only a mesh or interference
  check shows it.
- **`ModifyDefinition` answers `True` and still costs you the session on
  2024.** Nothing before the close says anything is wrong.
- **Put the ratio in `AddMate5`'s order, not in the order you read it.** Putting
  the new count into the field that held the old one, alone or with the other
  field as read, made the inverse ratio (2026's first run).

## What it does not do

- **Open: the remake on 2024 in a clean session.** Both committed 2024 runs of
  the remake ran in a session that already held the assembly
  `ModifyDefinition` had stranded (the definition route ran first, on its own
  copy). A rerun on 2024 in a fresh session, remake first, is in flight and not
  yet recorded here.
- **Open: the 2024 rows of items marked "2024 caveat"** — the lock re-take with
  an axial offset, the put on a gear in two gear mates, the put with the lock
  on, the rename in [assemblies/02](02-mates-from-code.md) and the drive in
  [assemblies/10](10-mate-a-gear-train-that-turns.md) — ran on 2024 only in run
  20261114-040636, after the stranded assembly, which held the trains' shared
  skeleton part and gear part open. They agreed with 2026 in every reading.
- What a lock does on its next solve after a put made with it on was not
  measured (no drive followed).
- Only a tooth-count-like ratio change on one gear mate was tried. A remake on
  a gear that carries two gear mates is planned, not run.
- Trains only, not gear pairs with a centre-distance equation
  ([assemblies/02](02-mates-from-code.md)).

## Evidence

Gear-Generator probe tier 8, Python over pywin32 late binding.

- `motion_update`: SolidWorks 2026 34.0.0 (run 20261113-231301) and 34.1.1
  (20261114-034458), SolidWorks 2024 SP5 32.5.0 (20261113-223412, a freshly
  started session). `layout_move_carries_mates = True`;
  `mesh_phase_route = "Transform2 put with the gear mate on"`;
  `put_with_gear_mate_on_moves = {'input': 0.0, 'output': <the put's angle>}`;
  `turn_on_a_shaft_move = {'as_a_multiple_of_the_need': -1.0, …}` (for a 20°
  swing, the gear's turn and the turn the mesh needed agreed to 1e-8 in size and
  were opposite in sign);
  `lock_unsuppress_keeps_the_new_angle = True` (relative angle 11.0 while
  suppressed, after unsuppressing and after the drive);
  `axial_global_moves_gear = True` (the other seven gears moved 0.0 mm);
  suppression by `"SetSuppression2 this configuration, None"` every time.
- `lock_retake_offset`, `put_on_twice_meshed_gear` (with `lock_on_put_turns`):
  2026 34.1.1 (20261114-034458) and 2024 (20261114-040636).
  `lock_offset_kept = {'all Z+': True, 'middle Z-': True}` with
  `after_drive = {'along': 3.0, 'angle': 11.0, 'axis_off': 0.0, 'off_axis': 0.0}`;
  `put_on_twice_meshed_gear_holds = True`; `lock_on_put_turns` 7.0° for the put
  gear and 0.0 for its locked partner and every other gear.
- `gear_mate_ratio`: 2026 34.1.1 runs 20261114-034458 and 20261114-052417;
  2024 runs 20261114-040636 (37 passed, this item failed: `CloseDoc` raised
  `0x80010105`) and 20261114-051023 (a fresh session; both routes, each on its
  own copy, definition first). In 051023:
  `gear_mate_ratio_closes = {'both fields, the other way round': False, 'remake': True}`,
  the definition copy's close `{'closed': False, 'raised': '0x80010105 — The server threw an exception.'}`;
  on 2026 (052417) `{'both fields, the other way round': True, 'remake': True}`.
  Both versions: `definition_numerator_is_second_teeth = True`; the remade mate
  deleted by `"Select2 then EditDelete()"`; `AccessSelections` raised
  `AttributeError`; the output turned at the new ratio to 1e-6 while the other
  train in the same assembly kept the old one.

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
- [GOTCHAS §73, §96, §97, §98](../../GOTCHAS.md)
