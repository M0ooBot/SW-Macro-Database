---
id: G106
title: A gear mate between non-parallel axes: the `Flip` does not tell its sense; read it back
always: false
members: [AddMate5, IMateEntity2.EntityParams, IGearMateFeatureData.Reverse]
languages: [all]
---

`AddMate5` makes a gear mate between axes that meet at an angle or pass each
other, and it solves (status 1, nothing moves when it is made). But which way
it turns cannot be taken from `Flip`: on SolidWorks 2026, `Flip` False gave
`Reverse` False at 30°–90° between the own axes and True at 120°–150°, and the
right `Flip` was False for some meeting and skew pairs and True for others.
What told the sense in all 40 turned cases measured: the mate turns the two
components the same way about their `IMateEntity2.EntityParams` directions
exactly when `IGearMateFeatureData.Reverse` is True. Measured for meeting axes
at 30°–150° and skew axes at 60°–120° on plain cylinders (SolidWorks 2026
34.1.1), and with real teeth in three meshes on 2026 and 2024 SP5; outside
those ranges nothing is measured, and each entity pointed along its own
component's axis in every case. See
[assemblies/04](../entries/assemblies/04-mates-between-non-parallel-axes.md#a-gear-mate-between-axes-that-are-not-parallel).
