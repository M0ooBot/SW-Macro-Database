---
id: G101
title: The drag operator did not turn a gear train held by axis-coincident mates
always: false
members: [Drag]
languages: [all]
---

[assemblies/05](../entries/assemblies/05-test-motion-with-the-drag-operator.md)'s
recipe (`AddComponent(gear, False)`, `TransformType` 0, `UseAbsoluteTransform`
`False`, `DragMode` as it came, relative `Drag` steps, `EndDrag`), repeated call
for call on a mated gear train with its driving mates suppressed, turned **only
the dragged gear**, each case asking 10°: the output in 1, 10 and 30 steps; the
input; and the second gear of a locked compound pair, whose lock partner stayed
put too. Every `Drag` returned `True` and no mate reported an error. That
entry's case where a drag did carry through a gear mate differed in three ways
none of which was varied: its gears were concentric to sketch points (here
their axes were **coincident** with shaft axes), its mesh was a ring (internal)
gear (here external meshes only), and it dragged 30° (here 10°). Its own second
assembly, gears concentric to faces, showed no carry either. So that result
stands for its own assembly but must not be relied on for a gear train without
testing. Prove a train by
driving a mate through a global instead. SolidWorks 2026 (34.1.1) and 2024 SP5.
See [assemblies/05](../entries/assemblies/05-test-motion-with-the-drag-operator.md#a-third-assembly-a-mated-gear-train-on-2026-and-2024).
