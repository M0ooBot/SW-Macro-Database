---
id: G43
title: An angle dimension on the Top plane: give its placement point in model space
always: false
members: [IModelDoc2.AddDimension2]
languages: [all]
---

The Top plane's sketch x is model +X and its sketch **y is model −Z**
(`top_sketch_axes_in_model = {'x': [1.0, 0.0, 0.0], 'y': [0.0, 0.0, -1.0]}`).
An angle dimension between two lines on it, placed with
`IModelDoc2.AddDimension2` at a point inside the angle given in **model**
coordinates, read the angle, 29.999999999999996° for 30°. The probe's own
findings record that placed at that point's **sketch** coordinates, which lie
mirrored across X and outside the angle, it had read the supplement; that
earlier run's log is not among the evidence kept here, so that half is
unverified in this repo. Either way the dimension is created without complaint,
and a supplement linked to a global drives the geometry to the wrong angle.
SolidWorks 2026 (revision 34.0.0). See
[sketches/04](../entries/sketches/04-dimensions.md).
