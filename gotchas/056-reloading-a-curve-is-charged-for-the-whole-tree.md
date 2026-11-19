---
id: G56
title: Reloading a curve is charged for the whole tree below it
always: false
members: [IFeature.ModifyDefinition, LoadPointsFromFile, ISldWorks.CommandInProgress, IFeatureManager.EditRollback]
languages: [all]
---

`IFeature.ModifyDefinition` after `LoadPointsFromFile` cost **25 seconds per
curve** on a 397-feature part with the tree rolled forward — 39 curves, sixteen
and a half minutes, which was the whole of a seventeen-minute export. With or
without `ISldWorks.CommandInProgress`, which suppresses the *rebuild* and not
this.

Put the rollback bar just after the last curve first
(`IFeatureManager.EditRollback(4, name)`) and the same reload is **0.5
seconds**, because everything built on the curve is rolled back and has nothing
to say. SolidWorks 2026 SP0.0. See
[curves/12](../entries/curves/12-roll-the-tree-back-before-reloading.md).
