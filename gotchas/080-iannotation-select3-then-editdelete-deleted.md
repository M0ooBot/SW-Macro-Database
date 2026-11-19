---
id: G80
title: `IAnnotation.Select3` then `EditDelete` deleted nothing
always: false
members: [IAnnotation.Select3, EditDelete]
languages: [all]
---

Nine balloons, each `GetAnnotation().Select3(True, null)`, then one `EditDelete`:
no error, and nine balloons still there. `IModelDocExtension.SelectByID2` with
`"<note name>@<view name>"` and type `"NOTE"` selected all nine and the same
`EditDelete` removed them. Count before and after any delete. Centre marks, by
contrast, delete through `ICenterMark.Select`. SolidWorks 2024 SP5 (32.5.0). See
[drawings/03](../entries/drawings/03-notes-title-block-and-deleting-annotations.md#deleting-an-annotation).
