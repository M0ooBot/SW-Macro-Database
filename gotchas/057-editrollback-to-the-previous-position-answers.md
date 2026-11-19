---
id: G57
title: `EditRollback` to the previous position answers True and moves nothing
always: false
members: [IFeatureManager.EditRollback, IFeatureManager.GetRollbackBarPosition]
languages: [all]
---

`IFeatureManager.EditRollback(2, "")` —
`swMoveRollbackBarToPreviousPosition` — returned `True` in 0.1 s and left the
bar where it was. The part stayed rolled back, its lofts reading 0 faces and
0 mm², the splits and inserts under them gone from view, and two whole pushes
handed it back that way before it was noticed.

Roll to **End** (`1`) instead, and then ask
`IModelDoc2.FeatureByPositionReverse(0)` whether it `IsRolledBack` — that is a
genuine bool. `IFeatureManager.GetRollbackBarPosition`, which would have made
this visible, is not reachable through pywin32 late binding at all.
SolidWorks 2026 SP0.0. See
[curves/12](../entries/curves/12-roll-the-tree-back-before-reloading.md).
