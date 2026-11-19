---
id: G34
title: `SaveAs3` overwrites an existing file without a word
always: true
members: [IModelDocExtension.SaveAs3, IModelDoc2.SaveAs3]
languages: [all]
---

`IModelDocExtension.SaveAs3(path, 0, 1, null, null, out, out)` onto an existing
path returned `True` and replaced the file. With by-reference outs it returned a
plain `True`, not a tuple. `IModelDoc2.SaveAs3(path, 0, 1)` returned `0` while
the file was written. If overwriting would be wrong, check the path first. See
[documents/02](../entries/documents/02-save-as-and-close.md).
