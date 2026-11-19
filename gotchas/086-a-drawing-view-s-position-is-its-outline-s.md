---
id: G86
title: A drawing view's `Position` is its outline's centre, not its model's
always: false
members: [IView.Position]
languages: [all]
---

Two views of one assembly at the same `IView.Position` were offset on the sheet
by a part's travel, because one view's outline included an extra phantom position. Align views
by where each puts the model origin — `ModelToViewTransform.ArrayData` items 9
and 10 — not by `Position`. SolidWorks 2024 SP5 (32.5.0). See
[drawings/01](../entries/drawings/01-new-drawing-and-place-views.md#laying-views-out).
