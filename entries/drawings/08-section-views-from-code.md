---
id: drawings-08-section-views-from-code
title: Make a section view from code, pointing the right way, with parts left unsectioned
status: verified
verified_on: SolidWorks 2024 SP5 (32.5.0)
language: [python]
api: [IDrawingDoc.ActivateView, ISketchManager.CreateLine, IDrawingDoc.CreateSectionViewAt5, IView.GetXform, IView.Angle, IView.Position, IView.GetVisibleComponents, IView.GetSection, IDrSection.SetExcludedComponents, IDrSection.GetExcludedComponents, IModelDoc2.ForceRebuild3]
keywords: [section view, CreateSectionViewAt5, section line, cutting plane, sketch line in a view, view sketch coordinates, GetXform, section upside down, change direction, NotAligned, ExcludedComponents, shafts not hatched, unsectioned parts, rotated view, IView.Angle, section between spokes, aligned section tilted, swCreateSectionViewAtOptions_e, SetExcludedComponents, GetSection, DrSection, excluded components ignored, section not hatched, no hatching in PDF, hatch missing, ForceRebuild3, move section view, aligned section stuck, section direction]
answers: "How do I make a section view of a part or assembly from code — draw the cutting line where I mean, make it face the right way, and keep shafts unhatched?"
---

# Make a section view from code

## What this is for

A full section through a drawing view: a cutting line across the parent view,
the section view projected beside it, hatching on the cut faces, and
standard parts such as shafts left unsectioned. Three things go wrong silently:
the cutting line lands somewhere else, the section comes out looking from the
wrong side, and a diagonal cut produces a tilted view.

Attach as in [drawings/01](01-new-drawing-and-place-views.md#attaching).
Positions here are sheet **millimetres** in the helpers and **metres** in the
API calls.

## The cutting line is sketched in the view's own coordinates

Activate the parent view, sketch a line with `ISketchManager.CreateLine`, select
it, and call `IDrawingDoc.CreateSectionViewAt5`. `CreateLine` takes the
**view's sketch coordinates**, not sheet coordinates: a line given at sheet
x 45–175 mm, y 190 mm on a view rotated 90° landed vertical and about 80 mm off
the left edge of the sheet, and the section cut through nothing.

The mapping that put the line where it was meant: the sheet point is the view
position plus the view's rotation applied to the sketch point, scaled.
`IView.GetXform` gives `[x, y, scale]` (metres), and `IView.Angle` the
rotation in radians. Inverted:

```python
def to_sketch(v, X, Y):
    """sheet mm -> view sketch metres (sheet = pos + scale*Rot(angle)*sketch)."""
    xf = list(call(v, "GetXform")); a = call(v, "Angle"); s = xf[2]
    dx, dy = X / 1000 - xf[0], Y / 1000 - xf[1]
    c, sn = math.cos(-a), math.sin(-a)
    return ((c * dx - sn * dy) / s, (sn * dx + c * dy) / s)
def section(drw, v, X1, Y1, X2, Y2, at, label, excl, opts=0):
    sm = call(drw, "SketchManager"); drw.ActivateView(call(v, "GetName2")); call(drw, "ClearSelection2", True)
    a, b = to_sketch(v, X1, Y1), to_sketch(v, X2, Y2)
    ln = sm.CreateLine(a[0], a[1], 0, b[0], b[1], 0)
    call(drw, "ClearSelection2", True); ln.Select4(False, nul)
    sv = drw.CreateSectionViewAt5(at[0] / 1000, at[1] / 1000, 0, label, opts, VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, excl), 0)
    call(drw, "ClearSelection2", True); return sv
```

`GetXform` returned three numbers here, `[0.11, 0.19, 1.0]`, with no angle in
them; the angle came from `IView.Angle`. To find where a model point (say a
shaft axis) sits on the sheet, use `ModelToViewTransform` as in
[drawings/01](01-new-drawing-and-place-views.md#laying-views-out); its rotation
is the first nine items, by columns ([GOTCHAS §10](../../GOTCHAS.md)).

`CreateSectionViewAt5(x, y, z, label, options, excludedComponents, depth)`
returned the new view (`Type` 2, named `Section View A-A`).

## Facing the right way: option 4

The section looks along the side its arrows point to, and that decides which
way up the model comes out. A horizontal cut across a top view of an assembly,
placed below the parent, showed the assembly **upside down** (the base plate
at the top, parts hanging below). Placing it above the parent instead changed
nothing. Option `4` (`swCreateSectionView_ChangeDirection`) reversed the view
direction and the section came out right way up.

Read the result, not the call: compare where a part you know is above another
lands in the section's outline, or look at an exported picture.

## Parts left unsectioned

Drafting practice leaves shafts, pins and fasteners unhatched in a section. The
sixth argument takes them as an array of the **assembly's** `IComponent2`
objects (from `IAssemblyDoc.GetComponents`), typed as a dispatch array:

```python
asm = doc_by_title(ASM_TITLE)
excl = [c for c in call(asm, "GetComponents", True) if any(call(c, "Name2").startswith(p) for p in ("Shaft A", "Shaft B", "Ring"))]
sec = section(drw, top, x1, y, x2, y, (100, 258), "A", excl, 4)
```

The section drew those components whole and unhatched, and hatched the rest.
For a part drawing pass an empty list. **On a later run this argument was
ignored**; `IDrSection.SetExcludedComponents` worked instead (below).

## A cut that has to miss something: rotate the parent, not the line

A spoked gear cut on its vertical centreline goes straight through two
spokes, so the recess between them never shows. A line at 45° fixed the cut
but produced a tilted section; with option `1`
(`swCreateSectionView_NotAligned`) the view could be moved anywhere, but it
was **still drawn at 45°**, with every dimension on it running diagonally.

What worked: rotate the parent view by setting `IView.Angle` (radians), then
cut on its vertical centreline as usual. The section came out upright and
went between the spokes.

```python
v.Angle = math.radians(45); call(drw, "EditRebuild3")
```

After a rotation, `GetOutline` is the rotated view's bounding box, which is
larger than what is drawn: a 117 mm circle rotated 45° reported a box about
178 mm wide. Place labels from the model's sheet position, not from the
outline.

## Excluding components after the fact: `IDrSection.SetExcludedComponents`

On a later run the sixth argument of `CreateSectionViewAt5` was **ignored**.
An array of the assembly's `IComponent2` objects, read with the view's
configuration active, gave sections in which those parts were still hatched,
with options 0, 1, 4 and 5 alike. Passing the same array afterwards to the
view's `IDrSection` worked. `IView.GetSection` returns it, and
`SetExcludedComponents` is a method that late binding presents as a boolean
property, so it is reached through `Invoke`:

```python
def set_excluded(sv, comps):
    sec = call(sv, "GetSection"); o = sec._oleobj_; did = o.GetIDsOfNames("SetExcludedComponents")
    return o.Invoke(did, 0, pythoncom.DISPATCH_METHOD, True, VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, comps))
```

It returned `True`, and `call(sec, "GetExcludedComponents")` then listed the
components. After a `ForceRebuild3` (next section) the exported PDF drew them
whole and unhatched. Calling `sec.SetExcludedComponents(...)` directly raised
`'bool' object is not callable`.

**Open:** why the argument worked in the run above and not here. The visible
difference is that this assembly had four configurations and the views showed
non-default ones; the earlier one had one. Settle it by repeating the argument
on a one-configuration assembly in the same session.

The drafting convention is for cuts **along** a shaft, pin or fastener. A
section that cuts across a shaft hatches the shaft like anything else; exclude
only what the cut runs along.

## Hatching appears only after `ForceRebuild3` on the drawing

Sections created and saved to PDF straight away had **no hatching at all**:
every cut face was an outline. `IModelDoc2.ForceRebuild3(False)` on the drawing
before `SaveAs` filled them in; `EditRebuild3` alone did not. On one sheet with
several sections, only the first one created came out hatched, presumably
rebuilt by the operations that followed it. Force-rebuild every sheet before
exporting it.

## Moving a section off its alignment line needs option 1

A section created with option 0 or 4 stays aligned with its parent. Setting
`IView.Position` moved it along the alignment direction only; the other
coordinate snapped back to the parent's. Created with option `5` (1, not
aligned, plus 4) it could be placed anywhere. A section cut in another section
view, such as a cross-section of a lengthwise section, behaved the same way
with option 1.

## Which way it looks: the line's direction and option 4 together

On one view with a vertical cutting line, four combinations gave two
directions:

| Line sketched | Option | Looked toward |
|---|---|---|
| bottom to top | 0 | side A |
| bottom to top | 4 | side B |
| top to bottom | 0 | side B |
| top to bottom | 4 | side A |

Reversing the line or adding option 4 each flips the view; doing both cancels.
`call(view, "GetVisibleComponents")` (property-style through late binding)
told the two apart without exporting: a component lying wholly on one side of
the cut was listed only when the section looked toward it.

## What it does not do

- **Partial sections, offset sections and section depth** (options 2, 16 and
  the last argument) were not run.
- **Which side the arrows point by default** was not worked out in general;
  it is checked after the fact, as above.
- **Open:** whether a section made with option 1 can be rotated upright with
  `IView.Angle`. Not tried, because rotating the parent worked.

## Evidence

SolidWorks 2024 SP5 (`RevisionNumber` 32.5.0), drawings on an A3 template in
third-angle projection, built from Python over pywin32 and checked in exported
PDFs.

- A line sketched at sheet coordinates on a rotated view landed off the sheet;
  the same line passed through `to_sketch` ran through both intended shaft
  axes, which `ModelToViewTransform` put at (91.07, 190.0) and
  (123.61, 190.0) mm on the sheet.
- On an assembly, option 0 drew the section upside down whether it was placed
  above or below its parent; option 4 drew it right way up.
- Five components passed as excluded (three shafts and two retaining rings) were
  drawn whole and unhatched; the gears and plate were hatched.
- On part drawings of gears, a vertical cut through the centre produced
  sections whose cut-face lines gave face width, recess depth and diameters
  (see [drawings/09](09-add-dimensions-and-tolerances.md)). On a spoked gear,
  a 45° line with option 1 gave a section drawn at 45°; rotating the parent
  45° and cutting vertically gave an upright section showing the 2.2 mm recess.

Later run, SolidWorks 2024 SP5 (32.5.0), 2026-11-15, an assembly with four
configurations and section views of two of them:

- The `CreateSectionViewAt5` exclusion array left three components hatched
  under options 0, 1, 4 and 5; `SetExcludedComponents` through `Invoke`
  returned `True`, `GetExcludedComponents` listed the three, and the PDF
  showed them unhatched.
- PDFs exported without `ForceRebuild3` on the drawing showed no hatching on
  any section; after it, every cut face was hatched.
- An aligned section's `Position` put moved it along one axis only; with
  option 5 the same put placed it freely.
- The four line-direction and option combinations in the table above, each
  checked in an exported PDF and by `GetVisibleComponents`.

Names and paths are placeholders here.

## See also

- [drawings/01 — New drawing and place views](01-new-drawing-and-place-views.md) — `ModelToViewTransform`, view rotation, choosing the named view
- [drawings/09 — Add dimensions and tolerances](09-add-dimensions-and-tolerances.md) — dimensioning the cut faces
- [drawings/04 — Centre marks and centre lines](04-centre-marks-and-centre-lines.md)
- [GOTCHAS §10, §87, §88](../../GOTCHAS.md)
