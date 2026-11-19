---
id: G61
title: A knit asked for a solid can sew a sheet and still make a feature
always: false
members: [IFeatureManager.InsertSewRefSurface]
languages: [all]
---

`IFeatureManager.InsertSewRefSurface(True, True, False, 1e-4, 1e-4)` — with
`TryToFormSolid` `True` — took three sheet bodies to one sheet body, made a
`SewRefSurface` feature, and answered as though it had done what was asked.
The part gained **no** solid body, and the resulting body's
`GetMassProperties` volume slot read 439,803,896.6 mm³ against a real
2,551,504.3: a meaningless number off an unclosed shell.

Count `IPartDoc.GetBodies2(0, False)` before and after, and delete the knit if
the count did not go up. SolidWorks 2026 SP0.0. See
[surfacing/04](../entries/surfacing/04-cap-a-refused-loft-into-a-solid.md).
