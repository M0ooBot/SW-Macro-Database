---
id: G119
title: `IBSurfParamData.GetControlPoints` is 1-based, answers an empty array out of range, and on 2026 `Row` runs to `ControlPointColumnCount`
always: false
members: [IBSurfParamData.GetControlPoints, IBSurfParamData.ControlPointRowCount, IBSurfParamData.ControlPointColumnCount]
languages: [pywin32]
---

`IBSurfParamData.GetControlPoints(Row, Column)` (from
`ISurface.GetBSurfParams3`) gives one control point per call. Two things about its
indices fail silently, seen on SolidWorks 2026 (34.1.1) from Python over pywin32:

- **It is 1-based, and out of range it returns an empty array, not an error.**
  `GetControlPoints(0, 0)` came back empty.
- **The bounds are swapped against the counts' names.** The SolidWorks API help, as
  quoted by its search index, says "1 <= index of row <= ControlPointRowCount",
  likewise for columns, and that "The U direction of surface is in the row
  direction". What SolidWorks 2026 did: `ControlPointColumnCount` held the u pole
  count (`len(UKnots) - UOrder`) and `ControlPointRowCount` the v pole count, and a
  point came back only for `Row <= ControlPointColumnCount` and
  `Column <= ControlPointRowCount`. Looping as the help words it gave 16 points from
  a surface of 4 × 98 poles (counts: 98 rows, 4 columns) and 9,604 from one of
  179 × 98 (98 rows, 179 columns); every other call returned an empty array.
  `Row` did index u: a surface rebuilt with `Row` as u matched SolidWorks' own
  `ISurface.Evaluate` to 2.4e-13 mm, with `Column` as u it was hundreds of
  millimetres off.

What to do: take the pole counts from the knots, `n_u = len(UKnots) - UOrder` and
`n_v = len(VKnots) - VOrder`; check that they are the same pair as the two counts;
loop `Row` 1..`n_u` and `Column` 1..`n_v`; and **fail on any call that does not
return exactly `ControlPointDimension` numbers**. A reader that appends whatever
comes back loses most of the surface without a word. Only 2026 was tried; whether
2024 or 2025 swap the counts too is not known, and other bindings were not tried.
Code and evidence: [entries/reading/17](../entries/reading/17-read-exact-b-spline-geometry.md).
