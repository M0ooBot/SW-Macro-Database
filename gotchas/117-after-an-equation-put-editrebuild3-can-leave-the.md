---
id: G117
title: After an `Equation(i)` put, `EditRebuild3` can leave the geometry as it was
always: false
members: [IEquationMgr.Equation, IModelDoc2.EditRebuild3]
languages: [all]
---

On SolidWorks 2024 SP5 (32.5.0), three gear parts each had a backlash global
changed with the indexed put `IEquationMgr.Equation(i) = text` (the
`_put_indexed` route in
[connect/02](../entries/connect/02-attach-from-python.md#setting-an-indexed-property)),
and `Equation(i)` read the new text back in every one. `IModelDoc2.EditRebuild3`
then ran on each part, with no feature errors and one solid body afterwards, and
the parts were saved. In one part a bore-diameter global changed in the same
batch did reach the geometry: the bore measured Ø8.35 mm afterwards. **The
backlash change did not**: the part's volume read the same to 0.001 mm³ before
and after (8981.381 mm³ in one part), and nothing reported a problem.

A later pass ran `ForceRebuild3(False)` on each part with nothing else changed.
Two of the three parts changed volume, by 39.15 mm³ and 39.69 mm³. The third
part's geometry does not depend on that global, and its volume did not change.
Parts whose globals had been set by a routine that ends in `ForceRebuild3(False)`
showed no change under the same check. This run did not check whether the
difference is that the bore dimension is linked to its global directly while
the backlash reaches the teeth only through other equations.

After changing equations, rebuild the **part** with `ForceRebuild3(False)`, as
[equations/01](../entries/equations/01-global-variables-from-code.md) does. Do
not do this on an assembly: see [§93](093-forcerebuild3-false-on-an-assembly-marks-every.md).
Reading the equation back proves only the text. To notice the problem, measure
something the change should move, such as the volume from
[reading/10](../entries/reading/10-mass-properties-as-an-oracle.md), before
and after.
