---
id: G109
title: `SetSuppression2` per configuration straight after `AddConfiguration2` misreports both ways
always: false
members: [IFeature.SetSuppression2, AddConfiguration2]
languages: [all]
---

With no rebuild after adding configurations, the first
`IFeature.SetSuppression2(0, 3, names)` on a mate **raised `0x80010105` and
still took effect**, and the second **returned False and did nothing**, in
every run that reached them (four on 2026, one on 2024 SP5). After a top-only
rebuild every call returned True and did what it said. Rebuild first, ignore
the return value, and read each flag back with `IsSuppressed2(3, names)`. See
[assemblies/13](../entries/assemblies/13-assembly-configurations-from-code.md#a-mates-suppression-per-configuration).
