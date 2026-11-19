---
id: G46
title: `arctan` is refused; the inverse tangent is `atn`
always: false
members: [IEquationMgr.Add2]
languages: [all]
---

In the Equation Manager, `"Probe Arctan"= arctan ( 1 )` made `IEquationMgr.Add2`
return **-1**, while `"Probe Atn"= atn ( 1 )` was accepted and read 45 in a part
whose trig is degrees. `arcsin ( 0.5 )` and `arccos ( 0.5 )` were accepted and
read 30 and 60: inverse trig answers in the document's angle unit, as `sin`
takes it, and only the tangent has the short name. Nested,
`atn ( tan ( "Probe Alpha" ) / cos ( "Probe Beta" ) )` with 20 and 15 read
20.646896487046472 against 20.64689648704647 worked by hand. Not tried inside
an Equation Driven Curve, whose trig is radians (§29). SolidWorks 2026
(revision 34.0.0), runs 20260915-002812 and 20260915-023929. See
[equations/01](../entries/equations/01-global-variables-from-code.md).
