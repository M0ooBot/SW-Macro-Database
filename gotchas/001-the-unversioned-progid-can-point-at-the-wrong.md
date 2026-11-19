---
id: G1
title: The unversioned ProgID can point at the wrong SolidWorks
always: false
members: [GetObject, GetActiveObject]
languages: [all]
---

`GetObject(, "SldWorks.Application")` failed with error **429, ActiveX
component can't create object**, on a machine with SolidWorks visibly open.

It was not a permissions problem and not a sandboxing problem. Several major
versions were installed, and the registry looked like this:

| ProgID | CLSID | Version |
|---|---|---|
| `SldWorks.Application` | `{afbec3b2-…}` | 32 (SW 2024) |
| `SldWorks.Application.32` | `{afbec3b2-…}` | 32 (SW 2024) |
| `SldWorks.Application.34` | `{666aaee2-…}` | 34 (SW 2026) |

The unversioned ProgID resolved to the 2024 class id, so the Running Object
Table lookup searched for a class that was not running, while the live 2026
session sat registered under the other one.

**Two fixes, both in this repo.** Ask the registry which
`SldWorks.Application.*` ProgIDs exist and try them newest first, or skip
ProgIDs entirely and walk the Running Object Table matching on the moniker
name `SolidWorks_PID_<pid>`, which is the same across versions. See
[connect/01](../entries/connect/01-attach-from-vbscript.md) and
[connect/02](../entries/connect/02-attach-from-python.md).

**The general lesson:** a COM failure that looks like an environment or
elevation problem can just be a ProgID resolving to the wrong install.

**It happens in the other direction too.** On a machine with 2024, 2025 and
2026 installed and only 2024 running, the unversioned ProgID resolved to the
**2026** class id (`{666aaee2-…}`, the same as `SldWorks.Application.34`).
From PowerShell, `[Marshal]::GetActiveObject("SldWorks.Application")` failed
with **`0x800401E3 MK_E_UNAVAILABLE`**, "Operation unavailable", while
`GetActiveObject("SldWorks.Application.32")` attached. Whichever version
registered last wins the unversioned name; do not assume it is the newest or
the oldest. The ROT moniker attached on the first try.

One attempt with `.32` failed earlier in the same session, before it later
worked, and its error message came back empty, so why it failed is not known.
SolidWorks 2024 SP5 (32.5.0), 2026-10-01.
