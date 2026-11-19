---
id: G25
title: The default template can be another year's, and in inches
always: true
members: [ISldWorks.GetDocumentTemplate]
languages: [all]
---

On a SolidWorks 2026 session, `ISldWorks.GetDocumentTemplate(1, "", 0, 0, 0)`
returned `C:\ProgramData\SolidWorks\SOLIDWORKS 2025\templates\Part.prtdot`, and
a part made from it was in **inches** (`swUnitsLinear` 3). The assembly
template was the 2025 one too, also inches. The 2026 folder's own template was
millimetres.

It matters beyond dimensions typed by hand: **equations are in document
units.** A global of 30 linked to a dimension is 30 mm in a millimetre part and
30 inches in an inch one, and nothing errors either way. Read the new
document's units and set them:
`IModelDocExtension.SetUserPreferenceInteger(263, 0, 5)` (swUnitSystem, MMGS)
worked. See [documents/01](../entries/documents/01-new-part-from-template.md).
