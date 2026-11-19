---
id: G19
title: A folder is two features in the tree
always: false
members: [FirstFeature, GetNextFeature, IFeatureFolder.GetFeatures, GetFirstSubFeature]
languages: [all]
---

Walking `FirstFeature`/`GetNextFeature`, a folder appears as itself and again
as a closing tag after its contents, both typed `FtrFolder`. Nesting is the
depth between the two. Count the end tags or your contents will run on into
whatever follows the folder.

**Do not find the end tag by its name.** It is named after the folder's first,
automatic name — `Folder3___EndTag___`, whatever the folder is called now — and
after a renamed folder's part is reopened, SolidWorks reuses `Folder3` and names
the new tag `Folder3___EndTag___0`. A walk matching the `___EndTag___` suffix
(this file said to, until 2026-09-24) reads that tag as a folder opening, and
everything after it as inside. Both features answer `IFeatureFolder.GetFeatures`
with the same contents: the one that comes after its first item is the tag.
SolidWorks 2026 SP0.0.

Walk the top-level chain only. A walk that also descends into
`GetFirstSubFeature` drops absorbed features into the middle of a folder's
contents and the tags stop lining up.
