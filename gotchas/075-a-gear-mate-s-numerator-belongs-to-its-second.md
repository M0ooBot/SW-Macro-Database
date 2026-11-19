---
id: G75
title: A gear mate's numerator belongs to its *second* entity, and is not the geometry
always: false
members: [GearRatioNumerator, IMate2.MateEntity, EntityParams]
languages: [all]
---

Read back from `IGearMateFeatureData`, `GearRatioNumerator` goes with
`IMate2.MateEntity(1)` and the denominator with `MateEntity(0)`: a mate listing
(pinion, ring) had the ring's diameter as numerator, and dragging the ring
turned the pinion by that ratio. Every gear mate in the assembly fit. Reading it
the other way round makes a correct gear train look inconsistent. The ratio is
also only what was typed: an internal gear's picked face was about a third
larger than its mates said, and 1 : 1 "gear" mates joined faces of different
sizes. Never derive a ratio from `EntityParams`. SolidWorks 2024 SP5 (32.5.0). See
[assemblies/06](../entries/assemblies/06-read-every-mate.md#which-gear-the-numerator-belongs-to).
