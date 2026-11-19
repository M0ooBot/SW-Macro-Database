---
id: G18
title: `MoveToFolder` does not move anything
always: false
members: [IFeatureManager.MoveToFolder, InsertFeatureTreeFolder2]
languages: [all]
---

`IFeatureManager.MoveToFolder` returned `False` and changed nothing on
SolidWorks 2026: on a curve, on a plane, on a folder, into an empty folder and
into a full one, with and without the feature selected first, before and after
a rebuild. There is no error and no exception, only the return value.

The only call that puts features in a folder is
`InsertFeatureTreeFolder2`, and it wraps the current selection in a **new**
folder. So an arrangement is rebuilt rather than patched. This is affordable
because deleting a folder deletes only the folder: everything it held stays
where it was. See [curves/11](../entries/curves/11-feature-tree-folders.md).
