---
id: G118
title: `EditSuppress2` suppresses a mate in the active configuration only
always: false
members: [IModelDoc2.EditSuppress2]
languages: [all]
---

On SolidWorks 2024 SP5 (32.5.0), a top assembly had two configurations. A
concentric mate in it was selected with `IFeature.Select2(False, 0)` and
suppressed with `IModelDoc2.EditSuppress2` (reached by attribute access, see
[§55](055-a-zero-argument-member-that-returns-nothing-or.md)). The call returned
`True` and `IFeature.IsSuppressed` read `True`, and the active configuration
rebuilt with no mate errors. **The other configuration still had the mate
on**. When that configuration was checked later, the mate reported
`GetErrorCode2` 51, because the face it used had since been suppressed in the
part.

`IFeature.SetSuppression2(0, 2, None)` (2 is `swAllConfiguration`) returned
`True` and suppressed the mate in both configurations. After
`ShowConfiguration2` and a rebuild, each configuration read `IsSuppressed`
`True` and no mate errors.

To change a mate's suppression in every configuration, use
`SetSuppression2(action, 2, None)` rather than selecting it and calling
`EditSuppress2`. For named configurations see
[assemblies/13](../entries/assemblies/13-assembly-configurations-from-code.md#a-mates-suppression-per-configuration).
In either case, read the result back in each configuration.
