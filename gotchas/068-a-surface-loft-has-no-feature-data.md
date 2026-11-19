---
id: G68
title: A surface loft has no feature data
always: false
members: [IFeature.GetDefinition]
languages: [all]
---

`IFeature.GetDefinition` on a surface loft (`BlendRefSurface`) returns
`Nothing`; on a solid loft (`Blend`) it returns an object. A surface loft's
profiles and guides cannot be changed through its definition — keep the
profile count and names constant and reload the curves instead, which a loft
follows. SolidWorks 2026 SP0.0. See
[features/12](../entries/features/12-guided-loft.md).
