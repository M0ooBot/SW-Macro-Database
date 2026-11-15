---
id: sketches-02-3d-sketch-as-vba
title: Generate a 3D sketch as a VBA macro
status: partly-verified
verified_on: SolidWorks 2026 (34.1.1), opening and closing a 3D sketch and drawing one line in it from Python, step by step; SolidWorks 2024 SP5 (32.5.0) inside an application build, where only the resulting axis on the line was read; the VBA listings were not run
language: [vba, python]
api: [ISketchManager.Insert3DSketch, ISketchManager.CreateLine, ISketchManager.ActiveSketch, IModelDoc2.InsertAxis2, CreatePoint, CreateLine2, CreateSpline, AddConstraint]
keywords: [3d sketch, Insert3DSketch, Insert3DSketch2, AttributeError Insert3DSketch2, 3DProfileFeature, three coordinates, no plane, axis from a 3D sketch line, EXTSKETCHSEGMENT, spline on surface, CreateArc plane]
answers: "How do I emit a VBA macro that draws a 3D sketch?"
---

# Generate a 3D sketch as a VBA macro

**Status: partly verified.** Opening and closing a 3D sketch, and drawing a
line in it, ran from Python on SolidWorks 2026 and 2024 (below). The VBA
listings were not run, on the same terms as [sketches/01](01-2d-sketch-as-vba.md).

## Correction: the call is `ISketchManager.Insert3DSketch`, not `Insert3DSketch2`

This entry first named `Part.SketchManager.Insert3DSketch2` as the call that
opens a 3D sketch. That was wrong, and the listings below and
[`code/vba/Sketch3D.bas`](../../code/vba/Sketch3D.bas) have been corrected by
hand to `Insert3DSketch`; the corrected VBA has not been run.

- On SolidWorks 2026 (34.1.1), a late-bound Python call to
  `SketchManager.Insert3DSketch2` raised **`AttributeError:
  <unknown>.Insert3DSketch2`**: the sketch manager has no member of that name.
- **`ISketchManager.Insert3DSketch(True)`** opened a 3D sketch
  (`ISketchManager.ActiveSketch` then read a sketch), and the same call again
  closed it (`ActiveSketch` read `None`): a toggle, like `InsertSketch`. Seen on
  2026 (34.1.1) step by step, and on 2024 SP5 (32.5.0) inside an application's
  build that made the same calls.

The sequence that ran, each member with its interface, all lengths in
**metres**:

1. `IModelDoc2.SketchManager`; `ISketchManager.AddToDB = True` and
   `DisplayWhenAdded = False`.
2. `ISketchManager.Insert3DSketch(True)`: returned `None`; `ActiveSketch` was
   not `None`.
3. `ISketchManager.CreateLine(x1, y1, z1, x2, y2, z2)`: returned the
   `ISketchSegment`; `GetName` read `'Line1'`. (`CreateLine`, not the
   `CreateLine2` the VBA below uses; `CreateLine2` in a 3D sketch was not run.)
4. `ISketchManager.Insert3DSketch(True)` again: returned `None`; `ActiveSketch`
   read `None`. Then `AddToDB = False`, `DisplayWhenAdded = True`.
5. The one new top-level feature had type **`3DProfileFeature`** (a 2D
   sketch's is `ProfileFeature`); `IFeature.Name` renamed it and read back.
6. `IModelDocExtension.SelectByID2("Line1@<sketch name>", "EXTSKETCHSEGMENT", 0,
   0, 0, False, 0, None, 0)` returned `True`, one item selected, and
   `IModelDoc2.InsertAxis2(True)` made a `RefAxis` on the line.
   `IRefAxis.GetRefAxisParams` put it on the line to 0.0 mm, pointing from the
   line's start to its end; the same after a save, close and reopen.

## What changes from 2D

**No plane.** `CreatePoint`, `CreateLine2` and `CreateSpline` take three real
coordinates in space, so there is nothing to select before running the macro.
That removes the 2D version's standing hazard entirely.

```vb
Part.SketchManager.Insert3DSketch True

Set v_P_root = Part.SketchManager.CreatePoint(0.000000000, 0.000000000, 0.040000000)
Set v_P_tip  = Part.SketchManager.CreatePoint(0.260000000, 0.000000000, -0.010000000)

Set v_L_spar = Part.SketchManager.CreateLine2( _
        0.000000000, 0.000000000, 0.040000000, _
        0.260000000, 0.000000000, -0.010000000)
```

`Insert3DSketch` is a toggle in the same way `InsertSketch` is: call it again
to close (observed from Python, above).

Everything else — welding, relations, dimensions, the select-then-constrain
shape — is identical to the 2D case.

## Splines are the same, with real Z

```vb
Dim pts_SP_edge(8) As Double
pts_SP_edge(0) = 0.000000000 : pts_SP_edge(1) = 0.000000000 : pts_SP_edge(2) = 0.040000000
pts_SP_edge(3) = 0.120000000 : pts_SP_edge(4) = 0.055000000 : pts_SP_edge(5) = 0.030000000
pts_SP_edge(6) = 0.260000000 : pts_SP_edge(7) = 0.000000000 : pts_SP_edge(8) = -0.010000000
Dim v_SP_edge As Object
Set v_SP_edge = Part.SketchManager.CreateSpline(pts_SP_edge)
```

## Arcs and circles: the open question

Whether `CreateArc` and `CreateCircleByRadius` honour the plane implied by
their own three coordinates, or resolve against whatever 3D-sketch plane
happens to be active, **is not settled**. Public sources do not answer it and
it has not been tested.

The safe response is to refuse to guess. Draw every arc and circle by hand, and
still create its centre and endpoints live so the manual instruction can say
"snap to the point already drawn" rather than asking someone to retype
coordinates:

```vb
' C_ring: circle, centre P_mid, r=18mm, normal [1, 0, 0]
' SW-MANUAL: C_ring (circle) - CreateCircleByRadius's plane behaviour inside a 3D
' sketch is UNVERIFIED - drawn by hand rather than guessed. By hand:
'   1. select the already-created point for P_mid (its centre, 120.00, 55.00, 30.00 mm)
'   2. Tools > Sketch Entities > Circle, radius 18.00 mm, normal [1.0000, 0.0000, 0.0000]
'   3. Esc/Enter to finish
```

**If you settle this question, update this entry and downgrade the manual step
to a live call.** That is exactly the kind of finding this repo exists to keep.

## Spline on surface

There is no documented COM call to create a spline constrained to lie on a
surface. Unlike a style spline, though, a plain spline *is* callable, so an
honest approximation is available: sample the true curve densely, pin it exactly
at each control point, and emit `CreateSpline` through the samples with a
comment naming the face it should lie on.

That is a live call and a labelled approximation rather than a manual step.
Between the pinned points, SolidWorks' own interpolation takes over from yours,
and the two agree less as the spacing widens.

## Relations in 3D

The constraint vocabulary is mostly shared with 2D and uses the same constants.
The exception is `sgHORIZONTAL2D` and `sgVERTICAL2D`, whose names give away
that they are plane concepts. In a 3D sketch, "horizontal" is only meaningful
relative to something, so prefer relations that are intrinsically
three-dimensional: coincident, parallel, perpendicular, tangent, equal, fix.

## Full generated example

[`code/vba/Sketch3D.bas`](../../code/vba/Sketch3D.bas) — points, a construction
line, a spline through them, a circle deferred to a manual step, two relations,
one dimension. Note the header's counted manual steps.

## Evidence

- The step-by-step run: SolidWorks 2026 (34.1.1), Python over pywin32, a new
  part, 2026-11-14: `(b) ISketchManager.Insert3DSketch(True): None`, `(b)
  ActiveSketch is not None: True`, `(c) ISketchSegment.GetName: 'Line1'`, `(d)
  ActiveSketch is None afterwards: True`, `(f) new top-level features:
  [('3DSketch1', '3DProfileFeature')]`, `(h) selected count: 1`, `(i)
  IModelDoc2.InsertAxis2(True): True`, `(j) ... off the line 0.00e+00 mm`, and
  after the reopen `same as before 0.0e+00 mm`.
- The failure it corrects: an application build on SolidWorks 2026 (34.1.1),
  2026-11-14, stopped on `AttributeError: <unknown>.Insert3DSketch2.`
- SolidWorks 2024 SP5 (32.5.0), 2026-11-14: an application build that opens the
  3D sketch with `Insert3DSketch(True)` and makes an axis on its one line, read
  back on the line (`off 0.0e+00 mm`) along the slanted direction asked for
  (−0.5, 0.866025404, 0), and again after a reopen.

Not run: `CreatePoint`, `CreateLine2` and `CreateSpline` in a 3D sketch, and any
of the VBA in this entry. On 2024 the toggle and `ActiveSketch` were not read
step by step; only the axis the build made on the line was.

**Open:** the generator that wrote `code/vba/Sketch3D.bas` (in another
repository) still emits `Insert3DSketch2`. The file here was corrected by hand
and says so in its header; the generator's source needs the same correction,
or a fresh generation will bring the wrong call back.

## See also

- [sketches/01 — A 2D sketch as VBA](01-2d-sketch-as-vba.md)
- [sketches/06 — What the sketch API cannot do](06-what-the-sketch-api-cannot-do.md)
