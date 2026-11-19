---
id: G98
title: A put on a locked or gear-mated gear moves that gear alone, silently
always: false
members: [Transform2, SetTransformAndSolve2, Drag, DragAsUI]
languages: [all]
---

A `Transform2` put on one gear of a mated train turned that gear only: its gear
mate partners did not follow, its **lock** partner did not follow either, and no
mate reported an error after the rebuild; driven afterwards, the locked pair
turned together **at the put's new relative angle**, so the lock silently adopts
whatever relation it finds. `SetTransformAndSolve2` and
`IDragOperator` (`Drag`, `DragAsUI`, several settings; every call `True`) did
the same to the input gear. Suppress every lock of a train around a put; prove
a train's ratio by driving a mate through a global, not by moving a gear.
SolidWorks 2026 and 2024 SP5. See
[assemblies/11](../entries/assemblies/11-change-a-mated-gear-train.md) and
[assemblies/05](../entries/assemblies/05-test-motion-with-the-drag-operator.md#a-third-assembly-a-mated-gear-train-on-2026-and-2024)
(and §73).
