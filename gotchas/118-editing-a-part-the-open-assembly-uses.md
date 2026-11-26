---
id: G118
title: Editing a part the open assembly uses locks the assembly, and AddDimension2 on a hidden part crashed SolidWorks
always: false
members: [IModelDoc2.EditSketch, IModelDoc2.AddDimension2, IModelDocExtension.ChangeSketchPlane, IFeatureManager.InsertRefPlane, ISketchManager.InsertSketch]
languages: [all]
---

Code that edits the sketch or features of a part through that part's own
document, while an open assembly uses it, left the assembly showing "One of
the components of this assembly is in rollback state. The assembly is
inaccessible now." The user could then select nothing and had to restart.
SolidWorks 2024 SP5 (32.5.0), twice:

- **`InsertRefPlane` and `ChangeSketchPlane`** on a part opened with `OpenDoc6`.
- **`EditSketch` then `AddDimension2`** on a part open hidden as a reference.
  This one also **crashed SolidWorks in `slduiu.dll`** (0xc0000005). The call
  came back as `com_error` -2147417851 (0x80010105, "The server threw an
  exception").

`ISketchManager.InsertSketch(True)` did not leave the sketch on the hidden
part. `EditRebuild3` cleared `GetActiveSketch2`, but the lock still appeared
later.

What to do instead:
- Do not edit sketches or features of a part an open assembly uses.
- Change sizes through an existing driving dimension, or ask the user.
- Treat 0x80010105 as a crash: stop writing, and have the user save and restart.

See [assemblies/15](../entries/assemblies/15-edit-a-part-the-open-assembly-uses.md).
