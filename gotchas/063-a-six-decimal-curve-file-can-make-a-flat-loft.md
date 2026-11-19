---
id: G63
title: A six-decimal curve file can make a flat loft end "3D", and the solid loft is refused
always: false
members: [InsertProtrusionBlend2]
languages: [all]
---

Written to six decimals of a millimetre, a planar section stands up to 5e-7 mm
off its plane, and SolidWorks' test for a flat loft end is stricter than that.
On one wing 9 of 22 flat sections were refused as the end of a solid loft —
at random-looking places, neighbours of the same shape passing — and
`InsertProtrusionBlend2` said so only by returning `Nothing`. The Loft page
says it outright: *"A 3D section that does not bound a face or surface cannot
be used as an end section."* Written to ten decimals, every one lofted as a
solid. A surface loft never asks, so it builds either way and hides the cause.
SolidWorks 2026 SP0.0. See
[curves/01](../entries/curves/01-sldcrv-file-format.md).
