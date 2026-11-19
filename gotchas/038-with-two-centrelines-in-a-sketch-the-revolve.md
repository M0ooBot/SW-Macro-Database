---
id: G38
title: With two centrelines in a sketch, the revolve axis has to be selected, at mark 16
always: false
members: [IFeatureManager.FeatureRevolve2]
languages: [all]
---

`IFeatureManager.FeatureRevolve2` with only the sketch selected revolved about
the sketch's one centreline. A bevel blank's sketch has two construction lines,
and there the axis line was selected as well: `SelectByID2("Line2@<sketch>",
"EXTSKETCHSEGMENT", 0, 0, 0, True, 16, null, 0)` after the sketch, and the ring
weighed exactly 2π r A about the meant line. Mark 16 was the first mark tried
and worked; mark 4 and "sketch only" with two centrelines were never tried. A
revolve about the wrong line still returns a feature, so weigh it. SolidWorks
2026 (revision 34.0.0). See [features/05](../entries/features/05-revolve.md).
