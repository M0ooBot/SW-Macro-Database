---
id: G97
title: On SolidWorks 2024, a gear mate changed by `ModifyDefinition` strands its assembly
always: false
members: [IFeature.ModifyDefinition, CloseDoc]
languages: [all]
---

After `IFeature.ModifyDefinition` changed a gear mate's ratio (returning `True`,
and the ratio right), `CloseDoc` on that assembly raised `0x80010105` ("The
server threw an exception") on SolidWorks 2024 SP5, and later closes left it
open without a word, with its parts, until SolidWorks was killed — saved first
or not, and with that probe alone in a fresh session. SolidWorks 2026 closed
it normally. Delete the gear mate and add it again instead, which carried a new
ratio through a save, a close and a reopen on both versions, each in a fresh
session. See
[assemblies/11](../entries/assemblies/11-change-a-mated-gear-train.md#the-ratio-change-that-strands-an-assembly-on-2024).
