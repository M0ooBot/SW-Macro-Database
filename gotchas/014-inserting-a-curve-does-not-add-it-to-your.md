---
id: G14
title: Inserting a curve does not add it to your surface
always: false
members: [InsertCurveFile]
languages: [all]
---

`InsertCurveFile` creates the curve and stops. Adding it to a boundary surface
or loft is still a human job. (Making a *new* loft over curves from code is
not: [features/12](../entries/features/12-guided-loft.md), since 2026-09-16.
Adding a curve to a surface or loft that already exists still is.) An automatic insert therefore leaves a curve that
looks connected and is not, which is a quieter failure than a missing curve.
This is why insertion should be opt-in.
