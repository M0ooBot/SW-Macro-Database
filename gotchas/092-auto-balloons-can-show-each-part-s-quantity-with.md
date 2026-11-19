---
id: G92
title: Auto-balloons can show each part's quantity, with no option to turn it off
always: false
members: [AutoBalloon5, CreateBalloonOptions]
languages: [all]
---

`AutoBalloon5` drew the BOM quantity beside every balloon on one template, and
`IAutoBalloonOptions` has no quantity member. `InsertBOMBalloon2` with
`IBalloonOptions.ShowQuantity = False`, one balloon per selected edge, did
not. `CreateBalloonOptions` is property-style through late binding (§55).
SolidWorks 2024 SP5 (32.5.0). See
[drawings/02](../entries/drawings/02-bom-table-and-balloons.md#balloons-one-at-a-time-without-the-quantity).
