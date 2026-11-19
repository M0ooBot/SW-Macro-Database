---
id: G54
title: Walking the feature tree every second makes SolidWorks stutter
always: false
members: [FirstFeature, GetNextFeature]
languages: [all]
---

API calls are served on SolidWorks' own thread, the one that draws the view.
A once-a-second `FirstFeature`/`GetNextFeature` walk of a 120-feature part took
about 650 ms of that thread each second, and orbiting the model stuttered for
as long as the tool was open; nothing in the tool's own process showed it.
Poll `IModelDoc2.GetFeatureCount` and `GetUpdateStamp` instead (under a
millisecond together) and read the tree only when they move. SolidWorks 2026.
See [reading/11](../entries/reading/11-cheap-change-detection.md).
