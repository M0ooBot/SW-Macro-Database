---
id: G42
title: A point-to-plane distance mate is measured along the plane's normal
always: false
members: [AddMate5]
languages: [all]
---

A component origin placed 8 mm below another component's Top plane (y = −8 mm),
mated to that plane with an 8 mm distance and `AddMate5`'s `Flip` false, moved
to **y = +8 mm** on rebuild: 16 mm from where it was placed, with nothing
reported and the mate's `D1` reading 0.008 either way. With `Flip` (the third
argument) `True` it stayed at −8 mm. Pass the distance positive and flip it
when the point is on the plane's negative side. SolidWorks 2026 (revision
34.0.0). See [assemblies/04](../entries/assemblies/04-mates-between-non-parallel-axes.md).
