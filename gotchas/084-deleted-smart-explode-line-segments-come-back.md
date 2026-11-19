---
id: G84
title: Deleted smart-explode-line segments come back
always: false
members: [EditDelete, InsertExplodeLineSketch]
languages: [all]
---

Smart Explode Lines make a 3D sketch (`3DExplode1`, `ExplodeLineProfileFeature`).
Selecting five of its segments and `EditDelete` — inside
`InsertExplodeLineSketch` or by editing the feature — left the count unchanged,
and after the rebuild all five were there. Accept them, or make your own lines.
SolidWorks 2024 SP5 (32.5.0). See
[drawings/07](../entries/drawings/07-explode-lines-in-a-drawing-view.md#segments-you-do-not-want).
