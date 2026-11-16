---
id: features-02-cut-extrude
title: Cut-extrude a sketch through the part
status: verified
verified_on: SolidWorks 2026 (revision 34.0.0); a mid-plane cut from an offset plane on SolidWorks 2024 SP5 (32.5.0)
language: [python]
api: [IFeatureManager.FeatureCut4]
keywords: [FeatureCut4, cut extrude, through all, swEndCondThroughAll, swEndCondThroughAllBoth, 9, flip direction, cut removed nothing, returns None, hole, 27 arguments, mid plane, swEndCondMidPlane, 6, cut from an offset plane, relief groove, internal groove, cut a sliver returns None]
answers: "How do I cut-extrude a sketch through a part from code, and be sure it removed material?"
---

# Cut-extrude a sketch through the part

## What this is for

Holes, slots, tooth spaces: a closed sketch cut through the solid. The call is
`FeatureCut4`, 27 arguments, and the obvious setting — through all, in the
default direction — made nothing at all when the sketch sat on the face the
boss was extruded from. This entry gives the forms that did and did not work.

## The call

Select the sketch feature (as in [features/01](01-boss-extrude.md)), then
**IFeatureManager** `FeatureCut4`. From the tool's gear build:

```python
def cut_extrude(self, handle: str, sketch: str, name: str) -> str:
    """Through all, both directions (probe cut: the default direction removed nothing)."""
    doc = self._doc()
    self._select_feature(self._sketch_feature(sketch))
    end = findings.CUT_END_CONDITION
    feature = call(call(doc, "FeatureManager"), "FeatureCut4", False, False, False, end, end, 0.01, 0.01, False,
                   False, False, False, 0.0, 0.0, False, False, False, False, False, True, True, True, True,
                   False, 0, 0.0, False, False)
    call(doc, "ClearSelection2", True)
    if feature is None:
        raise SolidWorksError(f"FeatureCut4 would not cut {sketch} through the part as {name}.")
    kept = self._rename(feature, name)
    self._handles[handle] = {"feature": kept}
    return kept
```

with `CUT_END_CONDITION = 9  # swEndConditions_e.swEndCondThroughAllBoth`.

The probe built the 27 arguments from three choices:

```python
def _cut_args(single: bool, flip_direction: bool, end: int) -> Tuple[Any, ...]:
    """FeatureCut4's 27 arguments for a through cut, in the help's order."""
    return (single, False, flip_direction, end, end, 0.01, 0.01, False, False, False, False, 0.0, 0.0,
            False, False, False, False, False, True, True, True, True, False, 0, 0.0, False, False)
```

`single`, `flip_direction` and `end` are the probe's names for the first,
third, and fourth-and-fifth arguments; they are the only ones varied. The two
`0.01` depths are metres and unused by a through-all cut. It returns the new
feature, `GetTypeName2` `"ICE"`, or `None`.

## Why it is not obvious

A cylinder r 20 × 10 mm was extruded from the first reference plane; a circle
r 3 mm at x = 12 mm was sketched on that same plane; each form below was tried
on a fresh part. The expected removal is π × 3² × 10 = 282.743 mm³.

| Form | `single` | `flip` | `end` | Returned | Removed |
|---|---|---|---|---|---|
| through all, default direction | `True` | `False` | 1 | **`None`** | **0** |
| through all, direction flipped | `True` | `True` | 1 | `ICE` feature | 282.743 mm³ |
| through all both | `False` | `False` | 9 | `ICE` feature | 282.728 mm³ |
| through all, both ends | `False` | `False` | 1 | `ICE` feature | 282.728 mm³ |

**The default direction made nothing and said nothing.** No exception, just
`None`. From a sketch on the plane the boss grew from, "through all" in the
default direction presumably points away from the material, so there is
nothing to cut; that explanation is not established, only the result.

**Which way is "flipped" depends on where the sketch is.** Flipping worked
here because of how this sketch and this boss were placed. Through all in
**both** directions (end condition 9) removes the same hole without that
dependency, which is why the tool uses it.

**Check the volume, not the return.** A cut that returns a feature but removes
the wrong material is possible in principle; the only way this probe could tell
the forms apart was the volume before and after
([reading/10](../reading/10-mass-properties-as-an-oracle.md)).

## A mid-plane cut from an offset plane

A groove inside a bore, centred along the part: a plane offset from the Front
plane to the groove's middle, a circle on it, and a cut with end condition **6**
(`swEndCondMidPlane`) whose depth is the groove's whole width. On SolidWorks
2024 SP5 (32.5.0), 2026-11-16, on a 26 mm long internally toothed sleeve (its
Front plane at one end, its axis along Z), from the script that ran:

```python
front = None
f = slv.FirstFeature
while f is not None and front is None:
    if f.Name == "Front Plane": front = f
    f = f.GetNextFeature
call(slv, "ClearSelection2", True); front.Select2(False, 0)
plane = call(call(slv, "FeatureManager"), "InsertRefPlane", 8, 0.013, 0, 0.0, 0, 0.0)
a = plane.GetSpecificFeature2.Transform.ArrayData
print("  relief mid plane at part Z", round(a[11] * M, 3), "normal", [round(v, 3) for v in a[6:9]])
if abs(a[11] * M - 13) > 1e-6:
    raise SystemExit("STOP: the plane is not at Z +13; nothing cut, part left unsaved for a look")
plane.Name = "Relief Mid Plane"
call(slv, "ClearSelection2", True); plane.Select2(False, 0)
sm = call(slv, "SketchManager"); sm.InsertSketch(True)
sm.CreateCircleByRadius(0.0, 0.0, 0.0, 0.013); sm.InsertSketch(True)
sk = None
f = slv.FirstFeature
while f is not None:
    if f.GetTypeName2 == "ProfileFeature": sk = f
    f = f.GetNextFeature
sk.Name = "Relief Sketch"
call(slv, "ClearSelection2", True); sk.Select2(False, 0)
cut = call(call(slv, "FeatureManager"), "FeatureCut4", True, False, False, 6, 0, 0.016, 0.0, False, False, False, False,
           0.0, 0.0, False, False, False, False, False, True, True, True, True, False, 0, 0.0, False, False)
call(slv, "ClearSelection2", True)
if cut is None:
    raise SystemExit("STOP: the relief cut made nothing; part left unsaved for a look")
cut.Name = "Relief Bore"
slv.ForceRebuild3(False)
```

- `InsertRefPlane(8, 0.013, …)` (a distance, [features/08](08-offset-reference-plane.md))
  put the plane at part Z +13.0 mm, normal (0, 0, 1).
- The cut, first argument `True` (one direction), end condition `6`, depth
  `0.016` m, returned a feature. The part's volume went from 11456.7 to
  8981.4 mm³. Its cylindrical faces afterwards: the new r 13 mm face from
  Z 5 to 21 mm, and the tooth faces (r 9.375 and 12.375 mm) split into
  Z 0–5 and 21–26 mm. **The mid-plane depth is the whole width, centred on the
  sketch plane**: 16 mm about Z 13.
- The walk above takes the last `ProfileFeature` in the tree as the sketch
  just made; it was, here.

**A cut that would only skim an existing hole returned `None`.** On a part
whose bore was 7.9375 mm, an 8 mm circle on a plane square to the axis, cut
through all both ways (end condition 9, the form at the top of this entry),
made nothing. Changing the existing bore sketch's diameter dimension to 8 mm
instead did it (the bore's radius read 3.969, then 4.0 mm). The cut's sketch
was left behind and had to be deleted. Why the cut was refused (a ring
0.03 mm thick) was not looked into.

## What it does not do

- `IFeatureManager.FeatureCut3` was listed in the probe but never called.
- Only through-all cuts from a sketch on the boss's own base plane were tried
  in the probe; a mid-plane cut from an offset plane has since run
  ([above](#a-mid-plane-cut-from-an-offset-plane)). Blind cuts and the other
  arguments were not varied.
- The small difference between the flipped (282.743) and both-directions
  (282.728) removals was within the probe's 0.1 % tolerance and was not
  investigated.

## Evidence

SolidWorks 2026 (revision 34.0.0), Python over pywin32, probe run
20260914-180426, probe `cut` in
[`code/python/gear_generator/probe/p2_solid.py`](../../code/python/gear_generator/probe/p2_solid.py).

- `cut through all, default direction = {'made': False, 'removed_mm3': 0.0, 'type': None}`
- `cut through all, direction flipped = {'made': True, 'removed_mm3': 282.743, 'type': 'ICE'}`
- `cut through all both = {'made': True, 'removed_mm3': 282.728, 'type': 'ICE'}`
- `cut through all, both ends = {'made': True, 'removed_mm3': 282.728, 'type': 'ICE'}`
- `pattern`: a cut made with end condition 9 and patterned six times left
  10869.911 mm³, the blank less six holes.
- `end_to_end`: the gear's tooth space and bore were cut through `cut_extrude`
  above.

## See also

- [features/01 — Boss extrude](01-boss-extrude.md) — selecting the sketch, and the blank this cuts
- [features/03 — Circular pattern](03-circular-pattern.md) — patterning the cut
- [reading/10 — Mass properties as an oracle](../reading/10-mass-properties-as-an-oracle.md)
- [features/07 — Loft cut](07-loft-cut.md) — a cut whose section changes
- [GOTCHAS §32](../../GOTCHAS.md)
- [features/10 — Swept cut](10-swept-cut.md) — a cut along a path with a twist
- [features/08 — Offset reference plane](08-offset-reference-plane.md) — the plane the mid-plane cut is sketched on
