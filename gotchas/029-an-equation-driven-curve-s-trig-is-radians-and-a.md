---
id: G29
title: An Equation Driven Curve's trig is radians, and a degree conversion is refused
always: false
members: [ISketchManager.CreateEquationSpline2]
languages: [all]
---

`ISketchManager.CreateEquationSpline2` evaluates `cos ( t )` in radians, even
in a part whose Equation Manager evaluates `sin ( 90 )` as 1. The natural fix,
`cos ( t * 180 / pi )`, was refused in every spelling tried: the call returned
`None` and made no curve, with no error. Keep curve expressions in radians and
convert degree-valued globals in their own equations. Curve expressions are in
document units. See [sketches/07](../entries/sketches/07-equation-driven-curve.md).
