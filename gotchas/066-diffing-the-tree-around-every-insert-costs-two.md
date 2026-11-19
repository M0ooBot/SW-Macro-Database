---
id: G66
title: Diffing the tree around every insert costs two full listings
always: false
members: [InsertCurveFile, IModelDocExtension.GetLastFeatureAdded]
languages: [all]
---

Finding what `InsertCurveFile` (or any insert that returns a boolean) made by
listing the tree before and after cost 3.7 s a listing on a 560-feature part,
plus 2.9 s to walk to it again by name: ten seconds of bookkeeping around one
second of work, per curve. `IModelDoc2.GetFeatureCount` either side and
`IModelDocExtension.GetLastFeatureAdded` answer the same question in a
hundredth of a second, with the tree rolled back or not, and
`IPartDoc.FeatureByName` finds a feature in one call. SolidWorks 2026 SP0.0.
See [curves/02](../entries/curves/02-insert-curve-from-file.md),
[connect/08](../entries/connect/08-find-a-feature-by-name.md).
