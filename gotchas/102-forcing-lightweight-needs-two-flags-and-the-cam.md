---
id: G102
title: Forcing lightweight needs two flags, and the CAM add-in then blocks the open
always: false
members: [OpenDoc6]
languages: [all]
---

`OpenDoc6` with `swOpenDocOptions_LoadLightweight` (128) alone left every
component fully resolved. With `swOpenDocOptions_OverrideDefaultLoadLightweight`
(64) added, every component read lightweight (`GetSuppression2` 1), and the
SOLIDWORKS CAM add-in put up a modal "SOLIDWORKS CAM Error" box ("…loading of
lightweight parts has been detected") that blocked `OpenDoc6` until something
closed it. Worse, lightweight, a mated gear train's first drive (transforms
read, a global set, a top-only rebuild, transforms read again) read one gear at
−24.17° where 2.5° was right; after that step every component read 2 (fully
resolved), and which call resolved them was not separated. The wrong reading
may be a stale transform read while lightweight. Read `GetSuppression2` on every
component and require 2 before reading transforms, driving or changing a train.
SolidWorks 2026 (34.1.1) and 2024 SP5, with that add-in loaded. See
[assemblies/11](../entries/assemblies/11-change-a-mated-gear-train.md#with-the-components-lightweight).
