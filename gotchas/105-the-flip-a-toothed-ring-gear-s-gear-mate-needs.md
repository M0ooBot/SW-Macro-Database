---
id: G105
title: The `Flip` a toothed ring gear's gear mate needs differs between versions; read the mate back
always: false
members: [AddMate5, IGearMateFeatureData.Reverse, IMateEntity2.EntityParams]
languages: [all]
---

For a pinion inside a toothed internal ring gear, the `Flip` that `AddMate5`
needed for the pair to turn as it meshes was **opposite on SolidWorks 2026 and
2024**, and on each version, on opposite-sense shafts, it also differed
between spur and helical rings. Plain
annuli with no teeth, and external pairs, needed `Flip` False on both, so a test
on annuli misses it. No rule from what is known before the mate is made is right
on both versions. What does tell, in 52 of 52 cases on each version: read the
made mate back. It turns its gears as they mesh exactly when
`(IGearMateFeatureData.Reverse == the two IMateEntity2.EntityParams directions
point the same way) == internal`. Correct a wrong one by deleting it and adding
it again with the other `Flip`. Driven off its built phase, a wrong sense
interferes and a right one does not. A follow-up round found the same for
helical rings of the other hand and of 15°, a herringbone ring and a spur ring
with a shifted pinion (each opposite between the versions; these on one shaft
sense combination only), and `Flip` False for an external pair in every shaft
sense. There, the read marked no document, and it agreed with the drive read
straight after `AddMate5`, after a top-only rebuild, after a remake, after a
save and reopen, and under `CommandInProgress` (wrong-to-right remake under it
shown on 2026 only). A train mated right on 2024 and opened in 2026 kept its
stored `Reverse` and turned right (2024 to 2026 only; 2024 cannot open a 2026
file). Nor is the `Flip` stable for one ring on one version: on 2024 a ring
mate made straight after its pinion was moved 2 mm along its shaft (a put with
the other mates suppressed and a top-only rebuild) needed `Flip` True, where the
same mate made after a reopen, pinion unmoved, needed False; the cause (the
move, the put and rebuild, or the missing reopen) was not separated. Never
carry a `Flip` from one make to the next. The same holds for a 1 : 1 gear mate
between two components on one axis: the `Flip` that turned them together was
False on 2026 and True on 2024 in the case measured, and the read-back named it
on both ([assemblies/10](../entries/assemblies/10-mate-a-gear-train-that-turns.md#a-1--1-gear-mate-between-two-components-on-one-axis)). See
[assemblies/10](../entries/assemblies/10-mate-a-gear-train-that-turns.md#checking-a-gear-mates-sense-after-making-it).
