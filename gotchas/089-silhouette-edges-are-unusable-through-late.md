---
id: G89
title: Silhouette edges are unusable through late binding
always: false
members: [IView.GetVisibleEntities2, GetCurve, Select2]
languages: [pywin32, late-bound]
---

`IView.GetVisibleEntities2(null, 4)` returns a cylinder's silhouette edges, but
through pywin32 `GetCurve` returned `None`, `GetStartPoint` raised "The server
threw an exception" and `Select2` raised "Type mismatch". Dimension a shaft's
diameters in an end view instead, where they are circles. SolidWorks 2024 SP5
(32.5.0). See
[drawings/09](../entries/drawings/09-add-dimensions-and-tolerances.md#turned-parts-the-silhouette-edge-cannot-be-used).
