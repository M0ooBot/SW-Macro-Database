---
id: G58
title: `EditRebuild3` returns False whenever anything in the part is in error
always: false
members: [EditRebuild3, ForceRebuild3]
languages: [all]
---

Including features that were in error before you touched the part. A part
carrying 13 such features answered `False` to every `EditRebuild3` while doing
exactly what it was asked, geometry and all. The return is not "did not run",
and code that treats it as one stops for no reason.

While you are there: `EditRebuild3` was **0.8 s** where `ForceRebuild3(False)`
was **25 s** on that part, for geometry identical to twelve digits. Rebuild
what changed. SolidWorks 2026 SP0.0. See
[curves/08](../entries/curves/08-rebuild-once-at-the-end.md).
