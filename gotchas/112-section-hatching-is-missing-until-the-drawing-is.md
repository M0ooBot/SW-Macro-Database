---
id: G112
title: Section hatching is missing until the drawing is force-rebuilt
always: false
members: [ForceRebuild3, EditRebuild3]
languages: [all]
---

Section views saved to PDF straight after creation had no hatching on any cut
face. `ForceRebuild3(False)` on the drawing before `SaveAs` filled it in;
`EditRebuild3` did not. SolidWorks 2024 SP5 (32.5.0). See
[drawings/08](../entries/drawings/08-section-views-from-code.md#hatching-appears-only-after-forcerebuild3-on-the-drawing).
