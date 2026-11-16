---
id: assemblies-13-assembly-configurations-from-code
title: Add, show and delete assembly configurations from code, with mates and distances set per configuration
status: verified
verified_on: SolidWorks 2026 (34.1.1) and SolidWorks 2024 SP5 (32.5.0)
language: [python]
api: [IConfigurationManager.AddConfiguration2, IModelDoc2.AddConfiguration3, IConfigurationManager.ActiveConfiguration, IModelDoc2.ShowConfiguration2, IModelDoc2.DeleteConfiguration2, IModelDoc2.GetConfigurationNames, IFeature.SetSuppression2, IFeature.IsSuppressed2, IDimension.SetSystemValue3, IDimension.GetSystemValue3, IDimension.SystemValue, IAssemblyDoc.GetComponentByName, IComponent2.Transform2, IComponent2.IsFixed, IEquationMgr.Add2, IModelDoc2.GetSaveFlag]
keywords: [assembly configuration, AddConfiguration2, ShowConfiguration2, DeleteConfiguration2, configuration from code, stale component handle, Transform2 None, IsFixed False, GetComponentByName after configuration change, SetSuppression2 configuration, swSpecifyConfiguration 3, SetSuppression2 0x80010105, SetSuppression2 returns False, IsSuppressed2, mate made in another configuration, SetSystemValue3, GetSystemValue3, swSetValue_InSpecificConfigurations, distance per configuration, SystemValue does not follow configuration, GetSystemValue3 reads 0, Add2 returns -1, positions per configuration, component position per configuration, put per configuration, ShowConfiguration2 marks modified, swSetValue_InThisConfiguration 1, swSetValue_InAllConfigurations 2, SetSystemValue3 wrong configuration, per configuration value read back wrong, AddConfiguration3, tooth phase per configuration, align teeth in every configuration, gear mate suppressed in this configuration, swUnSuppressDependent 2, SetSuppression2 this configuration]
answers: "How do I add, show and delete assembly configurations from code, and give a mate's suppression or a distance mate's value per configuration, without stale component handles misleading me?"
---

# Add, show and delete assembly configurations from code, with mates and distances set per configuration

## What this is for

An assembly that has to stand in several states, such as a sliding part at
different places, or a coupling on in one state and off in another, each as a
configuration, built and checked by a macro. The calls are few. What costs time
is what they do on the side: component handles go stale without an error, the
first suppression calls after adding a configuration misreport, a new mate's
flags differ by configuration, and a dimension's plain value does not follow
the configuration shown.

Everything below was observed from Python over pywin32, late-bound, on
SolidWorks 2026 (34.1.1) and 2024 SP5 (32.5.0), and was the same on both
unless a point says otherwise. This entry has no listing: the calls were made
by a probe whose code is not in this repo, so they are given as the calls and
arguments that ran, each with its interface, and the results seen. Lengths are
in **metres** at the API.

## Adding, showing and deleting

- **Add.** `IConfigurationManager.AddConfiguration2(name, "", "", 0, "", "", True)`
  (from `IModelDoc2.ConfigurationManager`) returned an `IConfiguration` and made
  the new configuration the active one: `IConfigurationManager.ActiveConfiguration.Name`
  read the new name. No window appeared.
- **What a new configuration inherits.** A component that was fixed stayed
  fixed in each new configuration (`IComponent2.IsFixed` read True, through a
  freshly fetched handle; see below). Mates that were on before the
  configurations were added read on in every new one.
- **A mate made while a non-template configuration is active** (made with
  `AddMate5` with `Default`, `X` and `Y` present and `Y` active) came out
  **suppressed in `Default` and on in `X` and `Y`**: neither on everywhere nor
  only in the active one. Set every mate's flags explicitly and read them back.
- **Show.** `IModelDoc2.ShowConfiguration2(name)` returned True and the active
  name read back as asked. Shown when it was already active, it returned
  **False** with nothing wrong ([GOTCHAS §23](../../GOTCHAS.md)): judge by the
  active name, not the return. No window appeared on any show.
- **A show marks the assembly modified, and no part.** On a reopened file with
  every document unmodified, `IModelDoc2.GetSaveFlag` on the assembly went
  False → True straight after `ShowConfiguration2`, before any rebuild; every
  part stayed False. Closing it unsaved afterwards with `ISldWorks.CloseDoc`
  asked nothing, and the next open came up in the configuration it was saved in.
- **A top-only rebuild after each show was enough.** After
  `ShowConfiguration2` + `IModelDoc2.ForceRebuild3(True)`, each configuration's
  distance mates had placed the sliding component where that configuration
  says, and a drive turned the components that configuration couples.
- **Delete.** `IModelDoc2.DeleteConfiguration2("Default")` with another
  configuration active returned True, no window; `GetConfigurationNames` read
  only the others, the active one stayed active, and every other
  configuration's flags were unchanged.
- **Save and reopen.** `SaveAs3` (silent) of the assembly with several
  configurations raised no window, and the assembly read unmodified after it.
  `OpenDoc6` reopened it in the configuration that was active at the save, every
  document unmodified, every flag and value as saved. The only window was
  SolidWorks' load-progress box (no title, class `#32770`, "Opened 4 Components /
  Updating Assembly"), which closed itself after about half a second.

## Component handles go stale on every add and show

After **every** `AddConfiguration2` and **every** `ShowConfiguration2`, each
`IComponent2` held from before answered `Transform2` with **None** and
`IsFixed` with **False** (the fixed layout part's included). No exception, no
error code: a wrong answer.

- Fetched again with `IAssemblyDoc.GetComponentByName(name)`, every handle
  answered correctly: the frame, `IsFixed` True for the fixed part,
  `GetModelDoc2` and `Name2`.
- Handles held across `DeleteConfiguration2` of a configuration that was not
  active stayed good.
- On 2026, in two of four runs, a freshly fetched handle once answered
  `GetModelDoc2` with None, and once `Name2` with an empty string, so a
  selection string built from it named nothing. The passing runs (one on each
  version), which read both on every fresh handle, saw neither. The runs that
  passed selected after a change by full names read before any configuration
  existed: `IModelDocExtension.SelectByID2("<feature>@<component>@<assembly>",
  "PLANE" or "EXTSKETCHPOINT", 0, 0, 0, append, 1, None, 0)`.

So: **re-fetch every component by name after every add and show**, and build
selection strings from names you already hold.

## A mate's suppression per configuration

`IFeature.SetSuppression2(action, 3, names)` on a mate feature, with action
`0` (suppress) or `1` (unsuppress), `3` meaning the listed configurations
(`swInConfigurationOpts_e.swSpecifyConfiguration`), and `names` passed as
`VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_BSTR, [...])`. Read back with
`IFeature.IsSuppressed2(3, names)`: one flag per name, in the order given,
without showing any configuration.

- **Straight after `AddConfiguration2`, with no rebuild between, the first two
  calls misbehaved, in every run that reached them** (four on 2026, one on
  2024): the first, `SetSuppression2(0, 3, ["Y"])` on a distance mate,
  **raised `0x80010105`** ("The server threw an exception") **and still took
  effect** (the mate read suppressed in `Y`); the second, the same call on a
  gear mate, **returned False and did nothing**.
- After a top-only rebuild (`ForceRebuild3(True)`), every later call returned
  True and read back as meant, on both versions.
- So **rebuild after adding configurations, never trust the return value, and
  read every flag back** with `IsSuppressed2(3, names)` ([GOTCHAS §109](../../GOTCHAS.md)).
- The flags read back the same unshown, after each show, after deleting
  `Default`, and after a save and reopen.
- `IsSuppressed2(3, names)` reads marked no document.
- In a configuration where a mate is suppressed, the other reads still worked:
  the mate-group walk listed every mate, suppressed ones included, in creation
  order ([assemblies/06](06-read-every-mate.md)); `IsSuppressed2(1, …)` gave the
  active configuration's flags; no mate had a nonzero error code;
  and a suppressed gear mate's `Reverse` and `EntityParams` read normally.

## A distance mate's value per configuration

One distance mate, its dimension given a value per configuration:

- `IDimension.SetSystemValue3(value_m, 3, ["Y"])`, with `3` =
  `swSetValueInConfiguration_e.swSetValue_InSpecificConfigurations`, returned
  **0** (`swSetValue_Successful`). The signatures were read from `sldworks.tlb`:
  `SetSystemValue3(NewValue, WhichConfigurations, Config_names) -> int` and
  `GetSystemValue3(WhichConfigurations, Config_names) -> VARIANT`; the enum
  values from `swconst.tlb`.
- `IDimension.GetSystemValue3(3, ["Default", "X", "Y"])` read each
  configuration's value, in metres, **without showing it**.
- **It can set a configuration that is not active.** Setting `Y` while `X` was
  active returned 0; the component in `X` did not move, and showing `Y` put it
  at the new value.
- It survived a save and reopen, and the reads on the reopened file marked
  nothing.
- **Before a configuration has a value of its own, `GetSystemValue3` reads 0
  for it**: with `Y` active and no per-configuration value set yet, it read
  `Default` 0, `X` 0, `Y` 10 mm. Set every configuration's value before reading
  any.
- **`IDimension.SystemValue` does not follow the configuration shown.** It read
  30 mm in `X` while the component stood at `X`'s 10 mm. Use `GetSystemValue3`
  with the configuration's name ([GOTCHAS §110](../../GOTCHAS.md)).
- **Linking the dimension to a global instead failed with several
  configurations present.** `IEquationMgr.Add2` with the link
  `"D1@<mate>" = "<global>"` returned **−1** while three configurations existed;
  the same call had linked another mate's `D1` while only `Default` existed. The
  global itself went in. `IEquationMgr.Add3`, which the API help names for
  documents with several configurations, was not tried.

## Where components stand in each configuration

**Measured here, on both versions: a component put by `Transform2` in one
configuration holds its own position in each configuration, and keeps it
through a save and reopen.** This qualifies [GOTCHAS §83](../../GOTCHAS.md)
and [assemblies/07](07-configurations-that-hold-different-positions.md),
which say component positions are not stored per configuration. The two
observations come from different procedures and have not been reconciled.

What this test did:

- Two components were each held by an axis mate and a distance mate along that
  axis, so the only freedom the mates left was the turn about the axis. One of
  them (F) had no gear mate anywhere; the other (D) had a 1 : 1 gear mate to a
  sleeve that was on in configuration `X` and suppressed in `Y`.
- With `Y` active, F was turned +20° and D +5° about their own axes by a
  `Transform2` put on handles fetched after the last configuration change,
  then a top-only rebuild (`ForceRebuild3(True)`). Positions were always read
  through freshly fetched handles.
- Showing `X` (and rebuilding top-only): F and D at their positions from before
  the puts (0°). Showing `Y` again: F at 20°, D at 5°.
- F put +10° in `X`: `X`'s F read 10°, and showing `Y` found F still at 20°.
  **A put held in the active configuration only.**
- Saved, closed, reopened and shown `X`, `Y`, `X`: F at 10°, 20°, 10°; D at 0°,
  5°, 0°. No mate error and no window at any step.
- An earlier run of the same kind found the same for D alone: put +5° in `Y`
  with its gear mate suppressed there, it was back at its old angle when `X`
  was shown.
- **F is the clean case.** D's gear mate is on in `X`, the configuration it
  returns to its old angle in, so that return may be the gear mate re-solving
  rather than a stored position: D's result is consistent with positions kept
  per configuration, not proof of it.

Stale handles cannot explain this: a stale handle answers `Transform2` with
None, not with an older position.

What §83's case was, by contrast: on the slider-crank-like mechanism of
assemblies/07, SolidWorks 2024 SP5, two configurations "whose only difference
was where a part had been dragged showed the same position". That drag sentence
records neither how the positions were set nor how they were read. The
instrumented reads in assemblies/07 (show, then `ForceRebuild3(False)`) were of
mates per configuration; its one instrumented "same position" was of an
attempt whose added mates left others in error (51), a different case.

**Not tried, and needed to reconcile the two:** a drag instead of a put; a full rebuild (`ForceRebuild3(False)`) after a show; a put on a component whose gear mate is on in every configuration; a component free to slide as well as turn.
Two later readings, on SolidWorks 2024 SP5: the per-configuration tooth
phasing [above](#teeth-in-phase-in-every-configuration) (a put with the gear
mate suppressed in that configuration only held there), and the drives and
drags of [assemblies/16](16-turn-a-mechanism-with-a-temporary-drive.md#putting-every-configuration-back)
(with the gear mates on everywhere, a solver move in one configuration reached
the others, and so did a drag undone by a put; which step did it was not
separated). Until the cases listed as not tried are run, do not rely on
either statement beyond its own procedure. A macro that needs a position in a configuration can still give that
configuration its own mates ([assemblies/07](07-configurations-that-hold-different-positions.md)),
which holds whichever way the open question falls.

## A dimension's value in this configuration, or in all

The other two values of `WhichConfigurations` were met on a 2024 SP5 assembly
with four configurations (`swSetValueInConfiguration_e`, read from
`swconst.tlb`: `1` `swSetValue_InThisConfiguration`, `2`
`swSetValue_InAllConfigurations`, `3` `swSetValue_InSpecificConfigurations`).

- **`2` with a one-name list does not set that configuration.** A distance
  mate's dimension was given four values in turn, each with its configuration's
  name, `dim.SetSystemValue3(v / M, 2, [k])`, then read back with
  `dim.GetSystemValue3(2, CFGS)`: **`[0.0, 40.5, 0.0, 0.0]`** mm for the four
  configurations, the second being the active one. The last value had landed
  in the active configuration and the others read 0 (no value of their own,
  [GOTCHAS §110](../../GOTCHAS.md)). `2` means all configurations; the name
  list is no limit. See [GOTCHAS §117](../../GOTCHAS.md).
- **Show each configuration and set it with `1` and `None`.** What put the
  right value in each:

  ```python
  for k in CFGS:
      asm.ShowConfiguration2(k)
      dim = mates()["Sleeve along Axis"].GetFirstDisplayDimension.GetDimension2(0)
      dim.SetSystemValue3(SLEEVE_D[k] / M, 1, None)
      asm.EditRebuild3
      zs = comps()["Sleeve-1"].Transform2.ArrayData[11] * M
      print(f"  [{k}] sleeve distance {dim.SystemValue * M:.3f} -> origin Z {zs:.3f} (want {-SLEEVE_D[k]})")
  ```

  (`mates()` and `comps()` walk the `MateGroup` and `GetComponents(True)`
  afresh, so the dimension and component handles are fetched after each show.)
  Each configuration's sleeve stood at its own distance, 55.5, 55.5, 48.0 and
  40.5 mm, and showing each configuration again read the same four.
- In a second assembly, the same `SetSystemValue3(v, 1, None)` with one
  configuration shown returned 0, and `GetSystemValue3(2, names)` then read
  `[41.75, 41.75, 35.75]` mm for its three configurations: the shown one read
  the new value and the other two the old 41.75 mm. Before the set, the same
  read had given `[0.0, 0.0, 41.75]`: only the configuration shown (one just
  added) read a value, and the other two read 0 ([GOTCHAS §110](../../GOTCHAS.md)).
- `GetSystemValue3(2, names)` (all configurations, with the list of names)
  read one value per name, as `3` does.

## Adding a configuration with `AddConfiguration3`

`IModelDoc2.AddConfiguration3(name, "", "", 0)`, called on the assembly's
document with `Default` shown, returned a configuration object, and the new
configuration became the active one (`ActiveConfiguration.Name` read it);
`GetConfigurationNames` listed it after the others. Its mates' suppression
came over from `Default` (a mate suppressed there read suppressed in the new
configurations too). Re-fetch every handle
afterwards ([GOTCHAS §108](../../GOTCHAS.md)); the scripts here walked the
components and mates again after every add and show.

## Teeth in phase in every configuration

A sliding toothed sleeve rides a toothed hub through a 1 : 1 gear mate
([assemblies/10](10-mate-a-gear-train-that-turns.md#a-1--1-gear-mate-between-two-components-on-one-axis));
each configuration puts the sleeve somewhere else along the axis. The gear
mate holds the two at whatever relative angle it was made at, so in
configurations where the teeth sat half a tooth out of phase they interfered.
Each configuration was put right on its own: suppress the gear mate **in this
configuration**, turn the hub by the error, rebuild, unsuppress it **in this
configuration**:

```python
P17 = 2 * math.pi / 17
def ang(c):
    a = c.Transform2.ArrayData
    return math.atan2(a[1], a[0])
def put_rot(c, theta, z):
    data = [math.cos(theta), math.sin(theta), 0.0, -math.sin(theta), math.cos(theta), 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, z / M, 1.0, 0.0, 0.0, 0.0]
    util = call(app, "GetMathUtility"); ole = util._oleobj_
    raw = ole.Invoke(ole.GetIDsOfNames("CreateTransform"), 0, pythoncom.DISPATCH_METHOD, True, VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, data))
    swcom._put(c, "Transform2", raw if hasattr(raw, "ArrayData") else _dynamic.Dispatch(raw))
asm.ShowConfiguration2("C2"); asm.EditRebuild3
cs = comps()
delta = ang(cs["Hub-1"]) - ang(cs["Sleeve-1"])
print(f"C2: hub - sleeve = {math.degrees(delta):.3f} deg (aligned there)")
gm = mates()["Sleeve rides Hub"]
for k in ("C1", "C3", "C4"):
    asm.ShowConfiguration2(k); asm.EditRebuild3
    cs = comps()
    cur = ang(cs["Hub-1"]) - ang(cs["Sleeve-1"])
    off = (cur - delta) % P17
    if off > P17 / 2: off -= P17
    print(f"[{k}] hub - sleeve = {math.degrees(cur):.3f} deg; off by {math.degrees(off):.3f} deg (mod one tooth)")
    gm = mates()["Sleeve rides Hub"]
    gm.SetSuppression2(0, 1, None); asm.EditRebuild3
    put_rot(cs["Hub-1"], ang(cs["Hub-1"]) - off, -55.5); asm.EditRebuild3
    gm = mates()["Sleeve rides Hub"]
    gm.SetSuppression2(2, 1, None); asm.EditRebuild3
    cs = comps()
    cur = ang(cs["Hub-1"]) - ang(cs["Sleeve-1"])
    off2 = (cur - delta) % P17
    if off2 > P17 / 2: off2 -= P17
    print(f"     now off by {math.degrees(off2):.4f} deg; hub Z {cs['Hub-1'].Transform2.ArrayData[11]*M:.3f}; mate suppressed here: {gm.IsSuppressed2(1, None)[0]}")
```

`P17` is one tooth of the 17-tooth pair; the phase that was right is the one
in `C2`, where the teeth were known to mesh. `SetSuppression2(0, 1, None)`
suppresses in the active configuration (`swInConfigurationOpts_e` `1`); the
unsuppress was given action `2`, `swUnSuppressDependent` in
`swFeatureSuppressionAction_e` (0 suppress, 1 unsuppress, 2 unsuppress with
dependents), and it unsuppressed the mate in that configuration
(`IsSuppressed2(1, None)` read `False`). The hub's axial position is put back
at its known Z in the same transform.

- The three configurations were off by 8.742°, 5.579° and 8.983°; after the
  step each read 0.0000° off, the hub still at its distance.
- **Each configuration kept its own phase.** Every configuration was then shown
  again in turn and checked for interference: before the step the sleeve and
  hub interfered in three of the four (17 interferences each, one per tooth,
  13.679, 8.054 and 13.971 mm³ apiece); after it, none in any, and no mate
  error in any. The gear mate was on in every configuration by then.
- A second assembly did the same with two pairs (a collar on a hub, and in one
  configuration the same collar engaging a dog), and also unsuppressed a mate
  in one configuration only with `SetSuppression2(2, 1, None)` (it returned
  `True`): `IsSuppressed2(2, names)` read `[True, True, False]`, on only in the
  configuration that was shown.

This is one more reading on the open question below: a put made while the
gear mate was suppressed **in the active configuration only** stayed in that
configuration, and the mate, unsuppressed, held it. Against it,
[assemblies/16](16-turn-a-mechanism-with-a-temporary-drive.md#putting-every-configuration-back)
saw a solver move in one configuration reach every other one, with the gear
mates on everywhere.

## What it does not do

- Showing a configuration whose mates over-define it was not tried.
- At most three configurations existed; derived configurations and design
  tables were not involved ([GOTCHAS §23](../../GOTCHAS.md) has what is known
  about those).
- A distance of 0 (a component on the reference plane) set per configuration,
  a slide not along +Z, and more than one per-configuration distance were not
  tried.
- Whether reading a suppressed gear mate's sense marks the document was not
  settled: it was read only while the assembly was already modified.
- What `SetSystemValue3` marks was not settled: the new assembly and its parts
  read modified throughout.

## Evidence

A configurations probe, run on SolidWorks 2026 (34.1.1) and on SolidWorks 2024
SP5 (32.5.0), each version in a session started fresh for it, 2026-11-14: the
first round runs 20261114-204436 (2026) and 20261114-232510 (2024), the
follow-up rounds 20261114-205913 (2026) and 20261114-233330 (2024); each passed
its configurations step. Three earlier 2026 attempts that stopped on the
probe's own use of stale handles are the source of the `GetModelDoc2` and
`Name2` cautions. Quoted from the logs, the same on both versions unless
marked:

- After `AddConfiguration2(X): returned 'CDispatch'`: `Transform2 of the held
  A: returned None`, `IsFixed of the held A: returned False`, the same for every
  held component and the layout; then `Name2 of the fresh A: returned '...-1'`,
  `GetModelDoc2 of the fresh A: returned 'CDispatch'`.
- `SetSuppression2(0, 3, ['Y']) on <distance mate>: raised 0x80010105 — The
  server threw an exception.`, then `SetSuppression2(0, 3, ['Y']) on <gear
  mate>: returned False`; after a rebuild six calls each `returned True`.
- Flags by `IsSuppressed2(3, ['Default', 'X', 'Y'])` (S = suppressed): the mate
  made while `Y` was active `SS-`, unchanged through every show, the delete
  (`S-` for `X`, `Y`) and the reopen.
- Shows `X`, `Y`, `X`: each `returned True`, no dialog, the sliding component
  at 10.0, 30.0, 10.0 mm. On the reopened file, `ShowConfiguration2` of the
  active `X` `returned: false`. `close_after_switch: {'dialog': false, 'how':
  'CloseDoc', 'seconds': 0.2}` on 2026, 0.18 s on 2024.
- `first: active on open: "X"`, every document's flag `false` on open.
- Per-configuration values: `before: {'Default': 0.0, 'X': 0.0, 'Y': 10.0}`,
  `set Y 30 while Y active: 0`, `after set: {'Default': 10.0, 'X': 10.0, 'Y':
  30.0}`, `set Y 35 while X active: 0`, `S_z_in_X: 10.0`, then `Y` 35.0;
  reopened `values: {'Default': 10.0, 'X': 10.0, 'Y': 35.0}`. `SystemValue`
  read 30 in `X` while the component stood at 10.
- The second distance mate's link by `Add2`: returned −1 with three
  configurations present.
- Positions: `in Y after the puts: {'D': 5.0, 'F': 20.0}`, `X shown: {'D': 0.0,
  'F': 0.0}`, `Y shown again: {'D': 5.0, 'F': 20.0}`, `X last: {'F': 10.0}`,
  `Y after the put in X: {'D': 5.0, 'F': 20.0}`; reopened shows `X`, `Y`, `X`:
  F 10.0, 20.0, 10.0 and D 0.0, 5.0, 0.0, `errors: {}`, `windows: []`
  throughout. The earlier round: `relative_in_Y_before_put: -6.0`,
  `relative_in_Y_after_put: -1.0`, `relative_in_X_after_show: -6.0`,
  `D_turn_from_put: 0.0`.

The per-configuration values with `1` and `2`, `AddConfiguration3` and the
tooth phasing come from two assemblies edited on SolidWorks 2024 SP5
(`RevisionNumber` 32.5.0) on 2026-11-16, Python over pywin32 launched from
WSL. From their output:

- `Sleeve along Axis now: [0.0, 40.5, 0.0, 0.0]` after the four calls with
  `2`; then, with `1` after each show, `[C1] sleeve distance 55.500 -> origin Z
  -55.500 (want -55.5)`, the same for `C2`, `[C3] … 48.000 -> origin Z -48.000`,
  `[C4] … 40.500 -> origin Z -40.500`, and the re-read after showing each again
  `-55.500`, `-55.500`, `-48.000`, `-40.500`.
- `AddConfiguration3(Open) -> <COMObject <unknown>> | active now Open | configs
  ['Default', 'Open']`, then the same for `Locked`; `before Locked edits: collar distance [0.0, 0.0, 41.75]
  | engage suppressed [True, True, True]`, `SetSystemValue3 35.75 -> 0`,
  `unsuppress engage -> True`, `after: collar distance [41.75, 41.75, 35.75] |
  engage suppressed [True, True, False]`.
- `C2: hub - sleeve = -10.588 deg (aligned there)`; `[C1] … off by 8.742 deg`,
  `now off by -0.0000 deg; hub Z -55.500; mate suppressed here: False`; `[C3]
  … 5.579`, `0.0000`; `[C4] … 8.983`, `-0.0000`; then for each configuration
  `mate errors none | interferences with sleeve/hub: none`, where before the
  step three configurations had listed 17 each.

Component and configuration names are placeholders here.

## See also

- [assemblies/07 — Configurations that hold different positions](07-configurations-that-hold-different-positions.md) — one configuration's own mates, and the positions question this entry qualifies
- [assemblies/06 — Read every mate](06-read-every-mate.md) — the mate-group walk, `IsSuppressed2`
- [assemblies/10 — Mate a gear train that turns](10-mate-a-gear-train-that-turns.md#a-1--1-gear-mate-between-two-components-on-one-axis) — the 1 : 1 collinear gear mate these configurations switched
- [assemblies/12 — Rebuild scope and the save flag](12-rebuild-scope-and-the-save-flag.md) — what marks a document
- [files/02 — Explode configurations](../files/02-explode-configurations.md) — configurations of a part
- [equations/02 — Link a dimension to a global](../equations/02-link-a-dimension-to-a-global.md)
- [assemblies/16 — Turn a mechanism with a temporary drive](16-turn-a-mechanism-with-a-temporary-drive.md) — positions that a drive changed in every configuration
- [assemblies/03 — Interference detection](03-interference-detection.md#which-components-an-interference-is-between) — the per-configuration phase check
- [GOTCHAS §23, §83, §108, §109, §110, §117, §119](../../GOTCHAS.md)
