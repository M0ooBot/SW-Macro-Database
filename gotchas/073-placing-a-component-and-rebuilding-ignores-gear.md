---
id: G73
title: Placing a component and rebuilding ignores gear mates
always: false
members: [Transform2, EditRebuild3]
languages: [all]
---

Setting a component's `Transform2` and calling `EditRebuild3` enforces
positional mates (a fully defined plate snapped back to 0°) but **not gear
mates**: a pinion placed 30° round left its gear-mated ring at 0°, with no mate
errors once the rest of the assembly was suppressed, and with many mates at
`GetErrorCode2` 51 otherwise. It also let a linkage arm sit at 10° that a drag
could only take to under 9°. To ask whether something can move, drag it with
`IDragOperator`; use a `Transform2` put only to restore a snapshot. SolidWorks
2024 SP5 (32.5.0). See
[assemblies/05](../entries/assemblies/05-test-motion-with-the-drag-operator.md).
