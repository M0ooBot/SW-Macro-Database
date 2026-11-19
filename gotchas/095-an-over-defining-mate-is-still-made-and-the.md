---
id: G95
title: An over-defining mate is still made, and the rebuild still says True
always: false
members: [AddMate5, ForceRebuild3, GetErrorCode2]
languages: [all]
---

`AddMate5` set its status to 5 (`swAddMateError_OverDefinedAssembly`) and
**made the mate anyway**; `ForceRebuild3` returned `True` afterwards. What
shows it: the new mate's `GetErrorCode2` with the warning flag `False`, the
mates it fights with the flag `True`, the component's `GetConstrainedStatus`
4, and `GetWhatsWrongCount` rising. The codes differ by version for the same
mates: 47 and 46 on SolidWorks 2026, 51 for all of them on 2024 SP5. Treat any
non-zero code as a problem and never read meaning into the number. See
[assemblies/02](../entries/assemblies/02-mates-from-code.md#when-a-mate-is-refused-or-over-defines)
(and §83 for 2024's error 5 earlier).
