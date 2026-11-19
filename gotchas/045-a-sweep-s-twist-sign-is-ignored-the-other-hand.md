---
id: G45
title: A sweep's twist sign is ignored: the other hand is `D1ReverseTwistDir`
always: false
members: [D1ReverseTwistDir, IFeatureManager.InsertProtrusionSwept4, InsertCutSwept5]
languages: [all]
---

`IFeatureManager.InsertProtrusionSwept4` with constant twist along path (8) and
a twist of **−π/2** made exactly the same solid as +π/2: the same volume,
565.6302 mm³, and the same centre of mass, (7.6397, +7.6400, 9.9998) mm, to
every printed digit. Both were a right-hand helix, turning counter-clockwise
about +Z as z increases, and so was a sweep whose path ran toward −Z. Nothing
reports that the sign was dropped. The direction is a flag on the definition:
`IFeature.GetDefinition`, `ISweepFeatureData.AccessSelections(doc, null)`,
`D1ReverseTwistDir = True`, then `IFeature.ModifyDefinition(data, doc, null)`,
which returned `True` and moved the centre to y −7.6401. The tool reverses its
`InsertCutSwept5` tooth spaces the same way, and a left-hand space came out
mirrored in y. SolidWorks 2026 (revision 34.0.0), runs 20260915-002812 and
20260915-023929. See [features/09](../entries/features/09-twisted-sweep.md) and
[features/10](../entries/features/10-swept-cut.md).
