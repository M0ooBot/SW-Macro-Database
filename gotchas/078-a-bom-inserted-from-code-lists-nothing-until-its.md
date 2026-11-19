---
id: G78
title: A BOM inserted from code lists nothing until its configuration is switched on
always: false
members: [IView.InsertBomTable5, SetConfigurations]
languages: [all]
---

`IView.InsertBomTable5` returned a table with a header row only — no QTY column,
no parts — because no configuration was visible in it
(`IBomFeature.GetConfigurationCount(True)` 0, `(False)` 1).
`SetConfigurations(True, [True], [name])` filled it: 10 rows × 4 columns. Nothing
in the insert's return says the table is empty. SolidWorks 2024 SP5 (32.5.0). See
[drawings/02](../entries/drawings/02-bom-table-and-balloons.md).
