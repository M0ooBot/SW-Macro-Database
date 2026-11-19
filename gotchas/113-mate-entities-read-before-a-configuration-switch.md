---
id: G113
title: Mate entities read before a configuration switch go stale
always: false
members: [ShowConfiguration2, AddMate5]
languages: [all]
---

Entities from an existing mate, read and then used after `ShowConfiguration2`,
gave `AddMate5` out code 1 but a mate with **no entities**, error 51, that
raised −2147417851 when selected. Delete it from a configuration where it is
suppressed, and read entities after switching. This is the mate-entity side
of §108. SolidWorks 2024 SP5 (32.5.0). See
[assemblies/07](../entries/assemblies/07-configurations-that-hold-different-positions.md#read-the-entities-after-switching-configuration).
