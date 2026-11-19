---
id: G96
title: A gear mate's ratio goes in first-selection-first and comes back reversed
always: false
members: [AddMate5, GearRatioNumerator, MateEntity]
languages: [all]
---

With `AddMate5(10, …, zFirst, zSecond, …)`, driving the first selected gear
30° turned the second 30·zFirst/zSecond: the numerator argument is the first
selection's tooth count. `IGearMateFeatureData` then read `GearRatioNumerator`
= zSecond (§75's rule: the numerator belongs to `MateEntity(1)`), and a ratio
put through the definition had to be given in `AddMate5`'s order again. `Flip`
False gave every external pair and every pinion in a plain annulus its own
sense, but not every toothed ring (§105); the alignment argument was ignored. SolidWorks 2026 and 2024 SP5. See
[assemblies/10](../entries/assemblies/10-mate-a-gear-train-that-turns.md#a-gear-mate).
