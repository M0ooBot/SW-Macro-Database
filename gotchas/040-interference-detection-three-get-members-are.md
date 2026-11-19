---
id: G40
title: Interference detection: three `Get` members are properties, `Done` is a method
always: false
members: [Done, GetInterferenceCount, GetInterferences, IInterference.Volume]
languages: [pywin32, late-bound]
---

On `IInterferenceDetectionMgr` through late binding, `GetInterferenceCount` and
`GetInterferences` came back as their values by attribute access, and so did
`IInterference.Volume` (cubic metres). `Done` came back as a Python `method`
and runs only as `manager.Done()` — the §31 trap again, on a member whose name
gives no hint. Also run the check on something that must fail: an
interference check that never reports anything looks exactly like a good fit.
SolidWorks 2026 (revision 34.0.0). See
[assemblies/03](../entries/assemblies/03-interference-detection.md).
