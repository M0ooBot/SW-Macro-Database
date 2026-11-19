---
id: G74
title: `swcom.connect()` refuses SolidWorks 2024 and 2025
always: false
members: []
languages: [pywin32]
---

`connect()` raised `WrongVersion: Found SolidWorks 2024 (revision 32.5.0). This
needs SolidWorks 2026 (revision 34) or newer.` with 2024 open. The floor
(`MINIMUM_MAJOR = 34`) is the Airfoil Converter's, the app `swcom.py` came
from, not a limit of the attach: a read-only tool taking its session from
`find_candidates()` read a whole 2024 SP5 assembly. Set the floor for your own
tool; do not lower the shared one. See
[connect/05](../entries/connect/05-choosing-among-versions.md#the-floor-belongs-to-the-application-not-to-swcom).
