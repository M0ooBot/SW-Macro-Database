---
schema: 2
id: assemblies-15-edit-a-part-the-open-assembly-uses
title: Editing a part that an open assembly uses — the rollback lock, and the crash on a hidden part
answers: "What happens when my code edits the sketch or features of a part that the user's open assembly uses, and what must it not do?"
keywords: [rollback state, assembly is inaccessible, one of the components of this assembly is in rollback state, cannot select components, EditSketch hidden document, AddDimension2 invisible document, slduiu.dll, access violation, 0xc0000005, -2147417851, 0x80010105, RPC_E_SERVERFAULT, the server threw an exception, InsertSketch does not exit, ChangeSketchPlane, InsertRefPlane, OpenDoc6 component part, part open as a reference, edit part in open assembly, live session, restart SolidWorks]
api: [IModelDoc2.EditSketch, IModelDoc2.AddDimension2, IModelDoc2.GetActiveSketch2, ISketchManager.InsertSketch, IModelDoc2.EditRebuild3, IModelDocExtension.ChangeSketchPlane, IFeatureManager.InsertRefPlane, ISldWorks.OpenDoc6]
language: [python]
status: partly-verified
verified_on: SolidWorks 2024 SP5 (32.5.0), two incidents in a user's live session (2026-11-25 and 2026-11-26)
majors: [32]
evidence: [2026-11-25-assemblies-15-edit-a-part-the-open-assembly-uses-python-32-a, 2026-11-26-assemblies-15-edit-a-part-the-open-assembly-uses-python-32-b]
recipe_status: null
recipe_evidence: []
superseded_by: null
---

# Editing a part that an open assembly uses

**Status: partly verified.** The two failures below happened on SolidWorks 2024
SP5 (32.5.0) and were traced in the Windows event log and in the dialog text
a watcher recorded. Neither was a planned probe. What to do instead is advice,
not a run; it is marked where it appears.

## What this is for

A user has an assembly open and asks for a change to one of its parts: a bore
size, a sketch plane. The part is already loaded, often **hidden** (open as a
reference of the assembly, `Visible` False), and it is tempting to edit it
through its own `IModelDoc2` from outside. Twice this left the user's assembly
unusable, and once it crashed SolidWorks. Both times the user had to restart
SolidWorks and lost what was unsaved.

## What the user saw

SolidWorks showed this message, and afterwards no component in the assembly
could be selected, moved or edited:

> One of the components of this assembly is in rollback state. The assembly is
> inaccessible now.

A part whose sketch is being edited, or whose feature tree is rolled back,
counts as "in rollback state". When the part has no window, the user has no way
to exit the sketch or roll it forward from the assembly.

## Incident 1: sketch plane and reference plane through the part's own document

A part of an open top assembly was opened through `OpenDoc6` and edited (2024
SP5, 32.5.0, pywin32 late binding, attached through the Running Object Table):

```python
md = app.OpenDoc6(RH, 1, 1, "", e, w)
ext = g(md, 'Extension'); fm = g(md, 'FeatureManager')
md.ClearSelection2(True)
a1 = ext.SelectByID2('Gear Axis', 'AXIS', 0, 0, 0, False, 0, NULLD, 0)
a2 = ext.SelectByID2('Right Plane', 'PLANE', 0, 0, 0, True, 1, NULLD, 0)
pl = fm.InsertRefPlane(4, 0, 16, THETA, 0, 0)
md.ClearSelection2(True)
pl.Name = 'Cross Pin Plane'
md.ClearSelection2(True)
s1 = ext.SelectByID2('Sketch2', 'SKETCH', 0, 0, 0, False, 0, NULLD, 0)
s2 = ext.SelectByID2('Cross Pin Plane', 'PLANE', 0, 0, 0, True, 0, NULLD, 0)
r = ext.ChangeSketchPlane(2, NULLD)
md.ClearSelection2(True)
md.EditRebuild3
```

(`g` reads a member as a property or calls it, and `NULLD` is
`VARIANT(VT_DISPATCH, None)`. `md.EditRebuild3` without brackets runs the
rebuild under pywin32 late binding: [connect/02](../connect/02-attach-from-python.md).)
The script went on to save the part, rebuild the top assembly, close the part
and re-activate the assembly. The script ran for 48 s, and the rollback message
appeared **19 s in**. Which call raised it was not recorded. There was **no
crash**: the editing alone was enough.

## Incident 2: `EditSketch` and `AddDimension2` on a hidden part

The aim was to dimension an undimensioned circle in a cut's sketch. The part was
hidden, as a reference of the open assembly (2024 SP5, 32.5.0, pywin32, `call`
from `swcom`):

```python
call(app,'SetUserPreferenceToggle',10,False)
skf = call(d,'FeatureByName','Sketch1')
call(d,'ClearSelection2',True)
res['sel_sketch'] = skf.Select2(False,0)
call(d,'EditSketch')
sk = call(d,'GetActiveSketch2')
segs = call(sk,'GetSketchSegments')
arc = segs[0]
cp = call(arc,'GetCenterPoint2'); c = [cp.X, cp.Y, cp.Z]; r = call(arc,'GetRadius')
call(d,'ClearSelection2',True)
res['sel_circle'] = arc.Select4(False, swcom._null_dispatch())
disp = call(d,'AddDimension2', c[0]+r*1.5, c[1]+r*1.5, 0.0)
```

- **`EditSketch` on the hidden part worked:** `GetActiveSketch2` returned the
  sketch.
- **`AddDimension2` crashed SolidWorks inside its own UI library.** The call
  raised `pywintypes.com_error` -2147417851 (0x80010105, "The server threw an
  exception") after about 12 s. At the same second the Windows Application log
  recorded event 1000 for SLDWORKS.exe: faulting module `slduiu.dll`, exception
  0xc0000005. Windows Error Reporting then filed APPCRASH reports, and a watcher
  saw SolidWorks hang for about 4 s. COM absorbed the crash and SolidWorks kept
  running, damaged.
- **The sketch did not close on request.** Two earlier runs had stopped partway
  (on a wrong member and on a type mismatch), each leaving the hidden part in
  sketch edit. `ISketchManager.InsertSketch(True)` did **not** leave it:
  `GetActiveSketch2` was still a sketch afterwards. `IModelDoc2.EditRebuild3`
  did clear `GetActiveSketch2`.
- **The lock appeared anyway, about 20 minutes later.** That was when the user
  next tried to use the assembly. The part was by then out of the sketch, not
  modified, and every feature read error 0. What state survived is not known.
  The crash, the earlier sketch edits, or both are the candidates.
- **The user had to restart.** Windows recorded SolidWorks as "stopped
  interacting with Windows" (AppHangB1) when it was closed. The hang carried the
  same Windows fault bucket as Incident 1's.

## What not to do

- **Do not edit a part's sketches or features through its own document while an
  open assembly uses it.** This covers `EditSketch`, `AddDimension2`,
  `ChangeSketchPlane` and `InsertRefPlane`, whether the part is hidden or was
  opened with `OpenDoc6`. Both incidents did exactly this.
- **Do not run sketch or dimension commands on an invisible document.**
  `AddDimension2` is a UI command: the API help routes it through the
  dimension dialog that `swInputDimValOnCreate` controls
  ([sketches/04](../sketches/04-dimensions.md)), and on a hidden part it
  crashed `slduiu.dll`.
- **Treat -2147417851 (0x80010105) as a SolidWorks crash, not a refused
  call.** Stop writing. Check the Windows Application log for an SLDWORKS
  event 1000, and tell the user to save and restart. Incident 2 followed the
  error with `InsertSketch`, `EditRebuild3` and further edits, which made the
  state harder to read and did not prevent the lock.

## What to do instead (advice, not run)

- **To change an existing size, change the driving dimension that controls it.**
  Use `IModelDoc2.Parameter(name)` and `IDimension.SystemValue`
  ([sketches/04](../sketches/04-dimensions.md)). That needs no sketch edit. Check
  first that a design table does not drive it (`IModelDoc2.GetDesignTable`):
  the second incident's part had one.
- **If no dimension drives the size, ask the user** to add one, or to make the
  change by hand in the part's own window.
- **Otherwise, edit only parts that nothing open uses.** For example, edit a
  closed part through a closed-file route, then let the assembly reload it.
- **After any write to a part, check that it is not left rolled back before
  handing control back:** `GetActiveSketch2` is `None`, and the last feature is
  not rolled back. The assembly's own state (`IsEditingSelf`, `GetEditTarget`)
  read normal while the lock was in place.

## If it has already happened

The user can right-click the component, choose **Open Part**, exit the sketch
or **Roll to End**, and switch back. That route was not tried here. If a call
has returned -2147417851, treat the session as untrustworthy: the user should
save their own work and restart SolidWorks.

## Evidence

- `2026-11-25-assemblies-15-edit-a-part-the-open-assembly-uses-python-32-a` — Incident 1, 2026-11-25, SolidWorks 2024 SP5 (32.5.0).
- `2026-11-26-assemblies-15-edit-a-part-the-open-assembly-uses-python-32-b` — Incident 2, 2026-11-26, SolidWorks 2024 SP5 (32.5.0).

Both were traced afterwards from:
- the Windows Application log (event 1000 and the AppHangB1 records),
- the WER report queue,
- the dialog text recorded by the SW-Agent watcher,
- the scripts as they ran.

## See also

- [sketches/04 — Add a dimension and set its value](../sketches/04-dimensions.md) — `AddDimension2`, `swInputDimValOnCreate`, `SystemValue`
- [assemblies/12 — Rebuild scope and the save flag](12-rebuild-scope-and-the-save-flag.md) — what an outside edit marks modified
- [curves/12 — Roll the tree back before reloading](../curves/12-roll-the-tree-back-before-reloading.md) — leaving a part rolled back on purpose, and putting the bar back
- [connect/02 — Attach from Python](../connect/02-attach-from-python.md) — members pywin32 runs with no brackets
- [GOTCHAS §51, §118](../../GOTCHAS.md)
