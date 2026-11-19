---
id: G67
title: Deleting a surface loft deletes the caps built on its edges
always: false
members: []
languages: [all]
---

Planar surfaces made across a surface loft's end edges go when the loft goes.
Code that deleted the loft and then asked for each cap by name failed on the
first (`No feature called ...`) after it had already deleted the knit, leaving
no loft at all. Delete in the reverse of building — knit, caps, surface —
checking each is still there. SolidWorks 2026 SP0.0. See
[surfacing/04](../entries/surfacing/04-cap-a-refused-loft-into-a-solid.md).
