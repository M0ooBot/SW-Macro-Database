---
id: G88
title: A section view can come out upside down, and a diagonal cut stays tilted
always: false
members: [CreateSectionViewAt5]
languages: [all]
---

`CreateSectionViewAt5` with option 0 drew an assembly section upside down,
wherever it was placed; option 4 (change direction) fixed it. A 45° cutting
line gave a section drawn at 45° even with option 1 (not aligned). Rotate the
parent view with `IView.Angle` and cut it straight instead. SolidWorks 2024 SP5
(32.5.0). See [drawings/08](../entries/drawings/08-section-views-from-code.md).
