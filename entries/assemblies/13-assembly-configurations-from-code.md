---
id: assemblies-13-assembly-configurations-from-code
title: Add, show and delete assembly configurations from code, with mates and distances set per configuration
status: verified
verified_on: SolidWorks 2026 (34.1.1) and SolidWorks 2024 SP5 (32.5.0)
language: [python]
api: [IConfigurationManager.AddConfiguration2, IConfigurationManager.ActiveConfiguration, IModelDoc2.ShowConfiguration2, IModelDoc2.DeleteConfiguration2, IModelDoc2.GetConfigurationNames, IFeature.SetSuppression2, IFeature.IsSuppressed2, IDimension.SetSystemValue3, IDimension.GetSystemValue3, IDimension.SystemValue, IAssemblyDoc.GetComponentByName, IComponent2.Transform2, IComponent2.IsFixed, IEquationMgr.Add2, IModelDoc2.GetSaveFlag]
keywords: [assembly configuration, AddConfiguration2, ShowConfiguration2, DeleteConfiguration2, configuration from code, stale component handle, Transform2 None, IsFixed False, GetComponentByName after configuration change, SetSuppression2 configuration, swSpecifyConfiguration 3, SetSuppression2 0x80010105, SetSuppression2 returns False, IsSuppressed2, mate made in another configuration, SetSystemValue3, GetSystemValue3, swSetValue_InSpecificConfigurations, distance per configuration, SystemValue does not follow configuration, GetSystemValue3 reads 0, Add2 returns -1, positions per configuration, component position per configuration, put per configuration, ShowConfiguration2 marks modified]
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
Until one of these is run, do not rely on either statement beyond its own
procedure. A macro that needs a position in a configuration can still give that
configuration its own mates ([assemblies/07](07-configurations-that-hold-different-positions.md)),
which holds whichever way the open question falls.

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

Component and configuration names are placeholders here.

## See also

- [assemblies/07 — Configurations that hold different positions](07-configurations-that-hold-different-positions.md) — one configuration's own mates, and the positions question this entry qualifies
- [assemblies/06 — Read every mate](06-read-every-mate.md) — the mate-group walk, `IsSuppressed2`
- [assemblies/10 — Mate a gear train that turns](10-mate-a-gear-train-that-turns.md#a-1--1-gear-mate-between-two-components-on-one-axis) — the 1 : 1 collinear gear mate these configurations switched
- [assemblies/12 — Rebuild scope and the save flag](12-rebuild-scope-and-the-save-flag.md) — what marks a document
- [files/02 — Explode configurations](../files/02-explode-configurations.md) — configurations of a part
- [equations/02 — Link a dimension to a global](../equations/02-link-a-dimension-to-a-global.md)
- [GOTCHAS §23, §83, §108, §109, §110](../../GOTCHAS.md)
