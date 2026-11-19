---
id: G108
title: Component handles go stale after every `AddConfiguration2` and `ShowConfiguration2`, silently
always: true
members: [AddConfiguration2, ShowConfiguration2, Transform2, IsFixed]
languages: [all]
---

After each add or show, every `IComponent2` held from before answered
`Transform2` with **None** and `IsFixed` with **False**, a fixed part's
included. No exception and no error code: a check such as "fix it unless
`IsFixed`" acts on a wrong answer. Re-fetch every component with
`IAssemblyDoc.GetComponentByName` after every add and show; those handles
answered correctly. Handles held across `DeleteConfiguration2` of a
configuration that was not active stayed good. SolidWorks 2026 (34.1.1) and
2024 SP5. See
[assemblies/13](../entries/assemblies/13-assembly-configurations-from-code.md#component-handles-go-stale-on-every-add-and-show).
