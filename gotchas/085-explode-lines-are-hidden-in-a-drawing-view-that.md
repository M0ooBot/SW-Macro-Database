---
id: G85
title: Explode lines are hidden in a drawing view that already existed
always: false
members: [UnblankSketch]
languages: [all]
---

An exploded drawing view did not show the assembly's explode lines. Selecting
the sketch through the view — `SelectByID2("3DExplode1@<root>-N@<view>", "SKETCH", …)`
— and `UnblankSketch` showed them. `UnblankSketch` returns nothing, so it must be
called, not reached by attribute ([§55](055-a-zero-argument-member-that-returns-nothing-or.md)).
SolidWorks 2024 SP5 (32.5.0). See
[drawings/07](../entries/drawings/07-explode-lines-in-a-drawing-view.md#showing-them-in-an-existing-view).
