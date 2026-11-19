---
id: G103
title: A suppressed mate reads error code 0, and unsuppressing an unsuppressed mate marks the assembly
always: false
members: [GetErrorCode2, SetSuppression2]
languages: [all]
---

`GetErrorCode2` on a suppressed mate read 0 with the warning flag `False`, even
for the mate that over-defined the assembly when it was on: a check that reads
only codes passes it. `SetSuppression2(1, 1, None)` on a mate already on returned
`True` and did nothing visible, yet `GetSaveFlag` read straight before and
straight after it, nothing in between, went from `False` to `True` for the
assembly alone: the call itself marks it. SolidWorks 2026 (34.1.1) and 2024
SP5. See
[assemblies/02](../entries/assemblies/02-mates-from-code.md#suppressed-mates-read-clean).
