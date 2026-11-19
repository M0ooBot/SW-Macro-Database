---
id: G62
title: Suppressing one feature suppresses what is built on it, and unsuppressing does not undo it
always: true
members: [IFeature.SetSuppression2]
languages: [all]
---

`IFeature.SetSuppression2(0, 1, None)` on one body feature — to write another
body alone to STEP — suppressed **74 other features**: the splits and inserts
built on that body, their folders, and the planes and sketches under those. The
part went from 16 solid bodies to 6. Unsuppressing the feature that had been
suppressed brought back **none** of them.

Restoring by name does not work either: one of the 74 is called `Sketch9<3>`,
which a name walk cannot find. Snapshot every feature's `IsSuppressed` with the
feature **objects**, in tree order, before; restore from that, parents first,
after. SolidWorks 2026 SP0.0. See
[reading/12](../entries/reading/12-snapshot-suppression-before-you-suppress.md).
