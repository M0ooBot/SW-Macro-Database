---
id: G87
title: A line sketched in a drawing view uses the view's coordinates
always: false
members: [ISketchManager.CreateLine]
languages: [all]
---

`ISketchManager.CreateLine` in an active drawing view takes the **view's sketch
coordinates**: offset from the view's position and turned by its rotation. A
section line given in sheet coordinates on a view rotated 90° landed off the
sheet and the section cut through nothing. Convert with `IView.GetXform`
(`[x, y, scale]`) and `IView.Angle`. SolidWorks 2024 SP5 (32.5.0). See
[drawings/08](../entries/drawings/08-section-views-from-code.md#the-cutting-line-is-sketched-in-the-views-own-coordinates).
