---
id: G53
title: A curve file with near-duplicate points is refused
always: false
members: []
languages: [all]
---

SolidWorks 2026 refused Curve Through XYZ Points files in which two
neighbouring points were all but coincident, as an offset or a trim leaves
them. Dropping every point within **0.01 mm** of the one kept before it
(keeping both ends) fixed it. A closed curve's deliberate repeat of its first
point as its last is fine. See
[curves/01](../entries/curves/01-sldcrv-file-format.md).
