---
id: G90
title: A Toolbox-flagged component reloads from the Toolbox library
always: false
members: [ReplaceComponents2]
languages: [all]
---

An assembly saved with an edited copy of a Toolbox part (status still 1) loaded
the **library** part on reopen, dropping the edits; its mates read clean until
a rebuild. Clearing the flag on the copy and re-saving the assembly was not
enough. Clear the flag, then `ReplaceComponents2` onto the copy, then save.
SolidWorks 2024 SP5 (32.5.0). See
[assemblies/09](../entries/assemblies/09-keep-an-edited-toolbox-copy.md).
