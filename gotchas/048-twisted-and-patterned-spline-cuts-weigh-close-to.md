---
id: G48
title: Twisted and patterned spline cuts weigh close to the arithmetic, not exactly
always: false
members: []
languages: [all]
---

Extrusions and straight cuts matched hand arithmetic to sixteen significant
figures ([reading/10](../entries/reading/10-mass-properties-as-an-oracle.md)).
Features with spline surfaces did not. A quarter-turn sweep of A·L =
565.487 mm³ measured 565.630 (2.5e-4 out). A twisted cut of 282.743 mm³
measured 282.743 when it started ahead of the face and 282.701 when it started
on it. Six patterned twisted cuts left 10869.773 mm³ against 10869.911. A ring
gear's single tooth-space cut weighed 157.494 mm³ on its own against 157.345
per space when sixty were patterned, which put the ring 2.8e-4 off "blank less
sixty spaces". None of these is an error in the feature. Compare such parts
with a relative tolerance (the Gear Generator uses 5e-4), or like with like: an
updated ring and a fresh build of the same ring agreed to 1e-13
(34284.14386641376 and 34284.143866418235 mm³). SolidWorks 2026 (revision
34.0.0), run 20260915-023929. See [features/09](../entries/features/09-twisted-sweep.md),
[features/10](../entries/features/10-swept-cut.md).
