---
id: G110
title: A dimension's value per configuration: `GetSystemValue3` reads 0 until set, and `SystemValue` ignores the configuration
always: false
members: [GetSystemValue3, IDimension.SetSystemValue3, IDimension.SystemValue, IEquationMgr.Add2]
languages: [all]
---

`IDimension.SetSystemValue3(m, 3, [name])` sets one configuration's value (it
returned 0, also for a configuration that was not active), and
`GetSystemValue3(3, names)` reads each without showing it. But before a
configuration has a value of its own, `GetSystemValue3` read **0** for it, and
`IDimension.SystemValue` read another configuration's 30 mm while the shown
one stood at 10 mm. Set every configuration's value before reading any, and
read with `GetSystemValue3` and the name. Linking the dimension to a global by
`IEquationMgr.Add2` instead returned −1 once several configurations existed.
SolidWorks 2026 (34.1.1) and 2024 SP5. See
[assemblies/13](../entries/assemblies/13-assembly-configurations-from-code.md#a-distance-mates-value-per-configuration).
