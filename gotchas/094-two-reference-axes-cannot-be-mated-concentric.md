---
id: G94
title: Two reference axes cannot be mated concentric
always: false
members: [AddMate5]
languages: [all]
---

`AddMate5` with `swMateCONCENTRIC` (1) between a component's reference axis and
another's returned `None`, made nothing, and set the status to 0
(`swAddMateError_ErrorUknown`), with no other message. `swMateCOINCIDENT` (0)
between the same two axes held the component on the axis; a cylindrical face
concentric with an axis also worked. SolidWorks 2026 (34.0.0, 34.1.1) and 2024
SP5 (32.5.0). See
[assemblies/10](../entries/assemblies/10-mate-a-gear-train-that-turns.md).
