---
id: G59
title: `AccessSelections` rolls the tree back, and the release that undoes it never ran
always: false
members: [AccessSelections, ReleaseSelectionAccess]
languages: [all]
---

Reading what a composite curve joins is not a read-only act:
`AccessSelections` on its feature data rolls the model back to just before the
feature (the help says so, and it is easy to read past). Afterwards the loft
built on that composite read 0 faces and the splits below it were gone.

`ReleaseSelectionAccess` puts it back — in 0.9 s — but it is a `Sub`, so late
binding hands it over as an uncalled method object and reaching it through a
helper that only fetches zero-argument members did nothing at all (§55). Every
push the tool made while that check existed left the part rolled back.
SolidWorks 2026 SP0.0. See [curves/06](../entries/curves/06-composite-curve.md).
