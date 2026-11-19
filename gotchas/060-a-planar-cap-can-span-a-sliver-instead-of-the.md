---
id: G60
title: A planar cap can span a sliver instead of the end, and answer True
always: false
members: [IModelDoc2.InsertPlanarRefSurface]
languages: [all]
---

`IModelDoc2.InsertPlanarRefSurface` across the four edges of a loft's end loop
returned `True` and made a `PlanarSurface` feature — of **0.078 mm²**, where
the section it was meant to close encloses **4,046.8 mm²**. It had capped a
sliver face's own little loop instead of the wing.

Compare the cap's `IFace2.GetArea` with the area the profile encloses, and
refuse a cap that is a fraction of it. Better still, refuse before capping:
count the edges of the end loop against the number of pieces the profile is
cut into — one edge per piece is what an end of a two-profile loft is.
SolidWorks 2026 SP0.0. See
[surfacing/04](../entries/surfacing/04-cap-a-refused-loft-into-a-solid.md).
