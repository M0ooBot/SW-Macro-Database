---
id: G69
title: The journal records a program's calls, but not all of them, and not always as made
always: false
members: []
languages: [all]
---

`%APPDATA%\SolidWorks\SOLIDWORKS 2026\swxJRNL.swj` records API calls an
external program makes over COM, next to what the user clicks, and is often
the only record of what a program did. But `IFeature.Select2` and renames
through `IFeature.Name` do not appear at all, a STEP export through
`IModelDocExtension.SaveAs` with the copy option appears as `Part.Save3`, and
only the current and previous sessions are kept. SolidWorks 2026 SP0.0. See
[reading/14](../entries/reading/14-the-journal-records-api-calls.md).
