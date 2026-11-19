---
id: G35
title: An entity drawn starting on another's end shares that point
always: false
members: [GetStartPoint2, GetSelectedObjectCount2]
languages: [all]
---

A line created starting exactly on a line's end, an arc's end, or an Equation
Driven Curve's end does not get a point of its own: there is one sketch point
there, and the line's `GetStartPoint2` compares equal to it. A coincident
relation between the two is already true, and trying to add it selects the same
point twice, leaving one object selected. Skip it. A line 0.1 mm away gets its
own point.

That second pick is where a careful selection helper goes wrong: one that judges
a selection by `GetSelectedObjectCount2` going up sees the count stay at 1 and
reports that the second entity could not be selected. Compare the two point
objects first (`a == b` was `True` for the shared point) and skip the relation
when they are the same. See [sketches/01](../entries/sketches/01-2d-sketch-as-vba.md) and
[sketches/07](../entries/sketches/07-equation-driven-curve.md).
