---
id: G44
title: A Move/Copy Body turn records no dimension, so no global can drive it
always: false
members: [IFeatureManager.InsertMoveCopyBody2]
languages: [all]
---

`IFeatureManager.InsertMoveCopyBody2(0, 0, 0, 0, 0, 0, 0, 0, radians(30), 0,
False, 1)`, with the body selected at mark 1 through `IBody2.Select2`, made a
`MoveCopyBody` feature (`Body-Move/Copy1`) and the body's centre of mass turned
30° about Y as expected, (19.82050807568877, ~0, −5.6698729810778055) mm from
(20, 0, 5). But the feature's dimensions were `[]`: the turn is not a dimension,
and an equation cannot change it. A part that has to follow a global angle has
to be built in its final orientation instead (planes and sketches that carry
the angle as dimensions: [features/06](../entries/features/06-reference-plane-normal-to-a-line.md),
[features/03](../entries/features/03-circular-pattern.md) for an axis from a line).
SolidWorks 2026 (revision 34.0.0), run 20260915-015506, probe
`move_body_rotate`, in
[`p2_bevel.py`](../code/python/gear_generator/probe/p2_bevel.py).
