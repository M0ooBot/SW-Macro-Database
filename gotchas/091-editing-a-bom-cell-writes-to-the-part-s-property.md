---
id: G91
title: Editing a BOM cell writes to the part's property
always: false
members: [Text]
languages: [all]
---

A `Text(row, col)` put on a BOM's DESCRIPTION cell changed the part's
`Description` custom property and left the part modified. On a read-only
Toolbox part it changed the configuration's property for the session only. Set
properties on the part, or add a column of your own with `InsertColumn2`.
SolidWorks 2024 SP5 (32.5.0). See
[drawings/02](../entries/drawings/02-bom-table-and-balloons.md#editing-a-bom-cell-writes-to-the-part).
