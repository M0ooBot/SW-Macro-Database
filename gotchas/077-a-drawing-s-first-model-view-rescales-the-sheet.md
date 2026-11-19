---
id: G77
title: A drawing's first model view rescales the sheet
always: false
members: [IDrawingDoc.CreateDrawViewFromModelView3, ISheet.SetScale]
languages: [all]
---

On a sheet set to 2:1 before any view, the first
`IDrawingDoc.CreateDrawViewFromModelView3` reset the **sheet** to suit the model
(2:1 came back 1:2) and placed its view at 0.5. Set `IView.UseSheetScale = True`
on the view and call `ISheet.SetScale` again *after* the first view, then read
`ScaleDecimal` on every view. SolidWorks 2024 SP5 (32.5.0). See
[drawings/01](../entries/drawings/01-new-drawing-and-place-views.md#one-model-view-then-projected-views-from-it).
