---
id: G76
title: Mate folders do not contain their mates
always: false
members: [GetFirstSubFeature, GetNextSubFeature, IMate2.Type]
languages: [all]
---

Under `MateGroup`, `GetFirstSubFeature` / `GetNextSubFeature` returns a folder's
mates as siblings between the folder's `FtrFolder` and its `___EndTag___`
(§19 again), and asking the folder for sub-features gave none: every record
came back at the top level. Track the nesting as a stack in walk order. End tag
names neither match their folder (`Folder3___EndTag___` closed a folder the
user had renamed)
nor are unique (`Folder1___EndTag___` twice in one assembly). Also,
`MateGearDim` is the gear mate's type name, and a limit distance mate shares
`IMate2.Type` 5 with a plain one. SolidWorks 2024 SP5 (32.5.0). See
[assemblies/06](../entries/assemblies/06-read-every-mate.md#folders-are-markers-not-parents).
