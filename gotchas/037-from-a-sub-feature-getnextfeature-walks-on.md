---
id: G37
title: From a sub-feature, `GetNextFeature` walks on through the main tree
always: false
members: [GetNextFeature, IFeature.GetFirstSubFeature, IFeature.GetNextSubFeature]
languages: [all]
---

A feature walk that descends with `IFeature.GetFirstSubFeature` and then steps
the children with `GetNextFeature` does not stay among the children. On
SolidWorks 2026 (revision 34.0.0) such a walk over a gear part listed a sketch
and the extrusion made from it five times over, then repeated the later features.
Step children with `IFeature.GetNextSubFeature`. Even then each consumed sketch
appears twice: in the top-level chain just before its feature, and as that
feature's sub-feature. See [connect/08](../entries/connect/08-find-a-feature-by-name.md).
