---
id: G115
title: In-context geometry is per part configuration, not per assembly configuration
always: false
members: [ReferencedConfiguration]
languages: [all]
---

Drawing views of two assembly configurations drew an in-context part at the
same size, the last one rebuilt. Give the part a configuration per state and set
each assembly configuration's `ReferencedConfiguration`. Reading the size from
the part document reported its own active configuration and hid the problem.
SolidWorks 2024 SP5 (32.5.0). See
[assemblies/14](../entries/assemblies/14-in-context-part-across-configurations.md).
