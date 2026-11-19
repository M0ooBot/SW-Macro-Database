---
id: G36
title: A new sketch point once could not be selected, and it did not happen again
always: false
members: [ISketchPoint.Select4]
languages: [all]
---

Observed once, cause unknown: an observation, not a rule. In a gear build on
SolidWorks 2026 (revision 34.0.0), the first relation in a freshly made part, a
circle's centre point to the origin, stopped the build with

```
od.centre could not be selected by Select4 or SelectByID2 (in Part249, with Part249 active and 0 selected).
```

By then the code had tried `ISketchPoint.Select4(False, null)` four times,
0.25 s apart, each judged by `ISelectionMgr.GetSelectedObjectCount2(-1)`, and
then `IModelDocExtension.SelectByID2("", "SKETCHPOINT", x, y, 0, ...)` at the
point's location. The part being built was the active document, and nothing was
selected. The session was shared with a person's own work: a user document that
was open when that build started had been closed by the time the next build
started. The next build, with the same code in the same session, went through.

Fourteen controlled trials did not reproduce it. Each made a new part, opened a
sketch on the first plane, drew a circle and selected its centre point: 8 in a
console process, rebuilds suppressed in every other trial, and 6 inside a Tk GUI
process through its COM worker thread, with rebuilds suppressed and the window
in front for three and withdrawn for three. Every one selected on the first
`Select4`, in 3 to 9 ms. A development run of a probe had earlier failed once
the same way on its first relation ("Entity 1 of 2 could not be selected by any
route"); the selection code it ran then is not recorded.

What held up: judge a selection by the count, retry briefly, fall back to a
second route, and when every route fails stop with a message naming the
document, the active document and the selection count. That message is what
ruled out the wrong document being active. The console trial script is
[`code/python/gear_generator/diagnostics/select_timing.py`](../code/python/gear_generator/diagnostics/select_timing.py).
See [sketches/03](../entries/sketches/03-relation-constants.md).
