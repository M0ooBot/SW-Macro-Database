---
id: G70
title: `DeleteDisplayStateSpecificRenderMaterial` wants two arrays, and says only `False`
always: false
members: [IModelDocExtension.DeleteDisplayStateSpecificRenderMaterial, IRenderMaterial.GetMaterialIds]
languages: [all]
---

`IModelDocExtension.DeleteDisplayStateSpecificRenderMaterial` takes the first
IDs of the appearances to delete as one array and their second IDs as another,
the two IDs coming from `IRenderMaterial.GetMaterialIds(out, out)`. Passed one
array holding both, `[11, 0]`, it returned `False` and deleted nothing. Passed
`[11]` and `[0]` it returned `True` and the appearance was gone. Reached by
attribute access it also runs once with no arguments first (§55). SolidWorks
2024 SP5 (32.5.0). See
[appearance/01](../entries/appearance/01-read-and-remove-a-part-appearance.md).
