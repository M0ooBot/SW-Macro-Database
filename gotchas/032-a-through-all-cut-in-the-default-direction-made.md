---
id: G32
title: A through-all cut in the default direction made nothing
always: false
members: [IFeatureManager.FeatureCut4]
languages: [all]
---

`IFeatureManager.FeatureCut4`, through all, single direction, default
direction, from a sketch on the plane the boss was extruded from: returned
`None`, removed nothing. Flipped, or through all in both directions (end
condition 9), it cut the hole. Measure the volume before and after rather than
trusting that a cut cut. See [features/02](../entries/features/02-cut-extrude.md)
and [reading/10](../entries/reading/10-mass-properties-as-an-oracle.md).
