---
id: assemblies-05-test-motion-with-the-drag-operator
title: Test whether an assembly can move, with the drag operator
status: partly-verified
verified_on: SolidWorks 2024 SP5 (32.5.0); the gear-train drags also on SolidWorks 2026 (revisions 34.0.0 and 34.1.1)
language: [python]
api: [IAssemblyDoc.GetDragOperator, IDragOperator.AddComponent, IDragOperator.TransformType, IDragOperator.UseAbsoluteTransform, IDragOperator.BeginDrag, IDragOperator.Drag, IDragOperator.EndDrag, IMateEntity2.EntityParams, IFeature.SetSuppression2, IFeature.GetErrorCode2, IComponent2.Transform2, IDragOperator.DragAsUI, IDragOperator.DragMode, IComponent2.SetTransformAndSolve2]
keywords: [gear mate does not propagate, DragAsUI, TransformType 0 1 2, drag operator, GetDragOperator, IDragOperator, BeginDrag, EndDrag, move component, rotate component, motion test, mechanism will not move, linkage locked, gear mate, mate diagnosis, which mate locks, suppress mate, EntityParams, error 51, Transform2 put, EditRebuild3, DragMode 0 1 2 3, SetTransformAndSolve2, gear train will not turn from code, drag does not carry through gear mate, lock mate drag, axis coincident]
answers: "How do I find out from code whether an assembly can move, and which mate is stopping it?"
---

# Test whether an assembly can move, with the drag operator

## What this is for

A mechanism that will not move in SolidWorks often shows no mate errors at all.
To find the mate that is stopping it, you need to try a motion, see how much of
it SolidWorks allows, and repeat with suspect mates suppressed one at a time.
Doing that by hand is slow. This entry does it from Python: a drag that behaves
like a mouse drag, measured afterwards, with every position and suppression put
back at the end.

## The call

All of it is on the assembly's `IAssemblyDoc` and the `IDragOperator` it hands
back. `swcom` and `maths` are the SW-Mates-Controller modules: `call` is the
late-binding helper (GOTCHAS §55), `create_transform` is the
`IMathUtility.CreateTransform` route from [assemblies/04](04-mates-between-non-parallel-axes.md),
and `maths.about_line(point, axis, degrees)` is a rotation about a line as a
frame. Points are in **metres**, angles in **degrees** for `about_line`.

```python
def drag(comp, line, deg, steps=10, recipe=None, watch=()):
    restore()
    op = call(doc, "GetDragOperator")
    call(op, "AddComponent", comps[comp], False)
    tt, absol, mode, how = recipe
    if tt is not None: op.TransformType = tt
    if absol is not None: op.UseAbsoluteTransform = absol
    if mode is not None: op.DragMode = mode
    call(op, "BeginDrag")
    oks = []
    for i in range(steps):
        d = deg / steps
        if absol:
            fr = maths.compose(maths.about_line(line[0], line[1], d * (i + 1)), snap[comp])
        else:
            fr = maths.about_line(line[0], line[1], d)
        xf = swcom.create_transform(app, fr)
        oks.append(getattr(op, how)(xf))
    call(op, "EndDrag")
    res = {w: round(rot(w), 2) for w in (comp,) + tuple(watch)}
    return oks, res, errors()
```

The recipe that ran is `(0, False, None, "Drag")`: `TransformType = 0`,
`UseAbsoluteTransform = False`, `DragMode` left as it came, and `Drag` given
each step as a **relative** transform, a rotation of `deg / steps` about a
fixed line in the assembly. `Drag` returned `True` on every step.

`rot(name)` is the angle between a component's frame now and its snapshot,
`acos((trace(R1·R0ᵀ) − 1) / 2)`. `restore()` puts every component back with a
`Transform2` put of its snapshot, then `EditRebuild3`:

```python
def restore():
    for n, k in comps.items(): k.Transform2 = swcom.create_transform(app, snap[n])
    call(doc, "EditRebuild3")
```

`errors()` reads `GetErrorCode2` on every unsuppressed mate, with the warning
flag passed as `VARIANT(VT_BYREF | VT_BOOL, False)`.

### Calibrate the recipe on two controls first

Before trusting any result, the probe dragged two components whose answer is
known, and used the first recipe that got both right:

| Control | Mates | Asked | Got |
|---|---|---|---|
| A disc hinged to a fixed bracket | concentric + coincident only | 30° about its axis | **30.0°** |
| A plate held by a coordinate-system mate | fully defined | 10° | **0.0°** |

The first recipe tried passed, so the other `TransformType`, absolute and
`DragAsUI` combinations were **never run**.

### Finding the axis to drag about

`IMateEntity2.EntityParams`, read from a mate that already references the
face, gives the axis directly in assembly coordinates, in metres:

```python
def axis_of(mate_name, idx):
    me = call(mates[mate_name], "GetSpecificFeature2").MateEntity(idx)
    p = list(me.EntityParams)
    return tuple(p[0:3]), maths.unit(p[3:6]), p
```

For a cylindrical face, items 0–2 are a point on the axis, 3–5 the direction
and 6 the radius. For a sketch point, the radius was 0. A concentric mate's
two faces gave the same axis.

### Suppressing a mate for one test

`IFeature.SetSuppression2(0, 1, None)` on a mate sub-feature suppressed it and
`SetSuppression2(1, 1, None)` brought it back, with `IsSuppressed` reading
`True` and `False`. Record every mate's `IsSuppressed` before you start, and in
a `finally` put back any that differ.

## Why it is not obvious

**Placing a component and rebuilding is not a motion test.** The obvious
shortcut is to set the component's `Transform2` to the turned frame and call
`EditRebuild3`. Positional mates are enforced: the fully-defined plate snapped
back to 0°. **Gear mates are not.** On the same assembly:

- A pinion placed 30° round turned its gear-mated ring gear 0°, and with the
  rest of the assembly's mates suppressed it reported **no mate errors at
  all**.
- With everything active, the same placement left many mates at
  `GetErrorCode2` = **51** with the warning flag `True`, and nothing moved.
- A linkage arm placed 10° round kept all 10° with no errors, while the
  drag operator on the same arm only reached **under 9°**. The placement hid
  the very resistance that was being looked for.

So use placement only to restore a snapshot, never to ask whether something
can move.

**A drag that only gets part of the way is the signal.** A jammed mechanism
does not usually refuse outright. It gives up part of each step. In the case
this came from, a 10° turn of a linkage arm reached under 9° and a 30° turn of
an output shaft about half that, both with no mate errors. Suppressing one mate at a time and dragging again,
the culprit was the one whose suppression gave the full 10° and 30°. That was
a tangent mate between two circular edges of a mated pinion and ring gear,
added next to their gear mate.

**Gear mates did carry motion through a drag** — in this assembly. (On a gear
train whose gears were held by axis-coincident mates, the same recipe, call for
call, did **not** carry through gear mates or a lock mate; the mate kind, the
mesh being internal or external, and the drag angle were not varied. See [the third assembly](#a-third-assembly-a-mated-gear-train-on-2026-and-2024)
and [GOTCHAS §101](../../GOTCHAS.md) before relying on a drag for a gear train.)
With the tangent mate suppressed, dragging the output 30° turned the ring gear 30° and back-drove
the pinion by 30° times the gear mate's
`GearRatioNumerator / GearRatioDenominator`. The numerator
is the ring gear's, the mate's *second* entity
([assemblies/06](06-read-every-mate.md#which-gear-the-numerator-belongs-to)).

## What it does not do

- **Dragging the driving gear did not drive the driven one.** Dragging the
  pinion 30° about its own axis turned it 30° with no tilt, but the ring gear
  stayed at 0°, both with and without the tangent mate. Dragging the ring gear
  12° the other way did drive the pinion. Why the gear mate carries motion one
  way and not the other under this recipe is **open**. The pinion and ring
  gear in that assembly were concentric to sketch points rather than axes,
  which is the first thing to rule out. A second recipe (`DragAsUI`, or another
  `TransformType`) is the second.
- **On a second assembly, no gear mate carried motion at all.** Four gears,
  each concentric to a cylindrical face (not a sketch point), joined by two
  gear mates that solved with no errors. Dragging any one of them 10° about its
  own axis turned that gear 10.0° and every other gear 0.0°, with `Drag` and
  with `DragAsUI`, at `TransformType` 0, 1 and 2 — twelve combinations on the
  two gears of one pair, and the plain recipe on all four. So concentricity to
  sketch points is not the explanation, and neither is the recipe choice among
  those tried. Testing gear-mate motion this way is **not reliable**; confirm a
  gear train's direction and ratio by dragging in the user interface.
- `DragMode` was never set in these two assemblies. It read 3 before every
  drag in the second one. It has since been set to 0, 1 and 2 on a third
  assembly, with no gear mate carrying motion at any of them (next section).
- The file is flagged modified (`GetSaveFlag` `True`) after a restore, even
  though every component was back within 0.01° and every mate's suppression
  matched the start. Do not save on the user's behalf. Tell them the contents
  are unchanged.
- The first two assemblies were run on SolidWorks 2024 only.

### A third assembly: a mated gear train, on 2026 and 2024

The Gear-Generator probe's tier 8 (`mated_train` in `p8_motion.py`) dragged the
input gear of a two-stage gear train mated as in
[assemblies/10](10-mate-a-gear-train-that-turns.md): every gear's axis
coincident with a skeleton part's shaft axis, a compound pair locked, two gear
mates with `Flip` False, every gear under-defined, one degree of freedom. The
input's drive mate was suppressed first, so nothing held the input but its
shaft. Driving that mate through a global turned the whole train at its ratio,
so the gear mates were solving. The drag, condensed from the probe (the same
calls and order; its logging removed and its helpers written out; not run as
written):

```python
import math
import pythoncom
import win32com.client.dynamic as dynamic
from win32com.client import VARIANT


def call(obj, name, *args):
    member = getattr(obj, name)
    return member(*args) if args else member


def read_member(obj, name):
    """A zero-argument member, read, and called only if late binding handed back a method."""
    value = call(obj, name)
    return value() if type(value).__name__ in ("method", "function") else value


def create_transform(app, data16):
    """IMathUtility.CreateTransform invoked as a method with a double array (assemblies/04)."""
    utility = call(app, "GetMathUtility")
    oleobj = utility._oleobj_
    raw = oleobj.Invoke(oleobj.GetIDsOfNames("CreateTransform"), 0, pythoncom.DISPATCH_METHOD, True,
                        VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, data16))
    return raw if hasattr(raw, "ArrayData") else dynamic.Dispatch(raw)


def turn_about_own_axis(component, degrees):
    """The relative move x' = R x + (p - R p): a turn about the component's own Z axis through its
    origin, as 16 numbers (rotation by columns, translation in metres, scale 1, three zeros)."""
    d = [float(v) for v in call(call(component, "Transform2"), "ArrayData")]
    axis, p = d[6:9], d[9:12]                    # the component's Z column, and its origin
    x, y, z = axis
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    k = 1.0 - c
    r = ((c + x * x * k, x * y * k - z * s, x * z * k + y * s),
         (y * x * k + z * s, c + y * y * k, y * z * k - x * s),
         (z * x * k - y * s, z * y * k + x * s, c + z * z * k))
    rp = [sum(r[i][j] * p[j] for j in range(3)) for i in range(3)]
    columns = [r[i][j] for j in range(3) for i in range(3)]
    return columns + [p[i] - rp[i] for i in range(3)] + [1.0, 0.0, 0.0, 0.0]


def drag(app, asm, component, degrees, method="Drag", setting=None):
    """IDragOperator, as a mouse drag would: one relative transform for the whole turn."""
    op = read_member(asm, "GetDragOperator")
    op.UseAbsoluteTransform = False
    if setting:                                  # e.g. ("TransformType", 1) or ("DragMode", 0)
        setattr(op, setting[0], setting[1])
    xform = create_transform(app, turn_about_own_axis(component, degrees))
    answers = [call(op, "AddComponent", component, False), read_member(op, "BeginDrag"),
               call(op, method, xform), read_member(op, "EndDrag")]
    return answers                               # every one answered True
```

One relative transform for the whole 20° turn about the gear's own axis (not
steps), `UseAbsoluteTransform = False`. The routes tried, in turn, on a train
with every shaft +Z and on one with the middle shaft −Z: `DragAsUI` and `Drag`
as the operator came (`TransformType` 0, `DragMode` 3, `IsDragSpecific`
`False`); `DragAsUI` with `TransformType` 1 and 2, and with `DragMode` 0, 1 and
2 (each read back as set); `IComponent2.SetTransformAndSolve2`; and a
`Transform2` put. **Every call answered `True`, and every route turned the
input 20.0° and every other gear 0.0°**, on SolidWorks 2026 (34.0.0 and 34.1.1)
and 2024 SP5 (32.5.0). A `Transform2` put on the *output* gear while the input
was driven also turned the output alone.

**This entry's own recipe, repeated on the same train.** A later probe
(`drag_operator_turns_train`) then repeated the recipe at the top of this entry
call for call on that train, its drive mates suppressed (so nothing held the
input but its gear mates): `GetDragOperator`,
`AddComponent(gear, False)`, `TransformType = 0`, `UseAbsoluteTransform = False`,
`DragMode` left as it came (3), `BeginDrag`, `Drag` with one relative turn per
step about the gear's own axis through its origin, `EndDrag`; positions put back
afterwards by `Transform2` and `EditRebuild3` (to 2.2e-16 mm). Each case asked
for 10° (30° on the output would have turned the input a whole turn):

| Dragged | Steps | Turned |
|---|---|---|
| The output gear | 10 | the output 10.0°, every other gear 0.0° |
| The output gear | 1, and 30 | the same |
| The input gear | 10 | the input 10.0°, every other gear 0.0° |
| The second gear of the compound pair (locked to the first) | 10 | that gear 10.0°, **its locked partner 0.0°** and every other gear 0.0° |

Every `Drag` returned `True`, no mate reported an error, nothing was left
selected and `CommandInProgress` read `False` afterwards; the same on
SolidWorks 2026 (34.1.1) and 2024 SP5, each in a session started fresh. So, on
this train, the number of steps and which end of it is dragged made no
difference.

**What still differs from the first assembly, none of it varied.** The first
assembly's success was the output dragged **30° in ten steps**, turning a
**ring (internal) gear** whose gear mate back-drove its pinion, with the gears
held **concentric to sketch points**. The repeat asked **10°**, on **external**
meshes only, with every gear held by its reference axis **coincident** with a
skeleton part's axis, and the trains' driving mates suppressed. Any of the mate
kind, internal against external mesh, or the drag angle may be the reason; which
is **open**. This entry's own second assembly, whose gears were concentric to
cylindrical faces, already showed no carry either. The first assembly's result
stands as observed; it does not carry over to a gear train without testing.
Settling it takes the same train with its gears held concentric (to sketch
points, then to faces), an internal mesh, and a 30° drag in ten steps. Until then, prove a gear train's ratio and direction by driving a mate
through a global
([assemblies/10](10-mate-a-gear-train-that-turns.md#one-degree-of-freedom-and-a-drive)),
and confirm a drag by hand in the user interface.

## Evidence

SolidWorks 2024 SP5 (32.5.0), a gear and linkage assembly of a few dozen
mates, driven from WSL through Windows Python
and pywin32 ([connect/10](../connect/10-driving-from-outside-windows.md)),
attached through the Running Object Table moniker (GOTCHAS §1: the unversioned
ProgID failed with `MK_E_UNAVAILABLE`).

- Controls as in the table above: 30.0° of 30° free, 0.0° of 10° fixed.
- Linkage arm 10°: under 9° as modelled. 10.0° with the tangent mate
  suppressed, the linked arm following through the coupler.
- Output 30°: about half as modelled. 30.0° with the tangent mate suppressed,
  the pinion turning by the gear ratio.
- Suppressing the other gear mates, a joint's second concentric mate, or the
  gear mate alone did not release the linkage. Only the tangent mate
  did.
- After every run, every component read back within 0.01° and 0.01 mm of its
  snapshot and no mate's suppression differed.

Second assembly, SolidWorks 2024 SP5 (32.5.0): eleven to thirteen mates, all
`GetErrorCode2` 0. Each drag of 5 steps × 2° returned `True` on every step;
the rotations read with `atan2` on the relative frame about the axis were 10.0°
for the dragged gear and 0.0° for the rest, every time. After restoring, the
worst residual was 0.0° and no mate had an error.

Third assembly (the mated gear train): Gear-Generator probe `mated_train`,
SolidWorks 2026 34.0.0 (run 20261113-231301) and 34.1.1 (run 20261114-034458),
SolidWorks 2024 SP5 32.5.0 (run 20261113-223412), Python over pywin32 late
binding. `drag_routes_the_train_follows = []` on all three; for every route
`dragged` read 20.0° for the input and 0.0° for each of the other three gears,
on both trains; `drag_operator` records
`AddComponent`, `BeginDrag`, `Drag`/`DragAsUI` and `EndDrag` all `True`;
`put_turns_a_gear_mated_gear_alone = True`. The recipe reproduced: probe
`drag_operator_turns_train`, SolidWorks 2026 34.1.1 (run 20261114-095421) and
2024 SP5 32.5.0 (run 20261114-102300), each 49 of 49 in a fresh session:
`drag_operator_turns_train = {'holds': False, 'recipes_that_held': []}`, five
cases each asking 10° (the output in 1, 10 and 30 steps, the input in 10, the
locked follower in 10),
`mate_kind = 'axis coincident …, not varied'`, every case's `Drag` list all
`True`, `errors {}`, `selected_after 0`, `command_in_progress_after False`,
`restored_after_mm` 2.2e-16. The result files are kept in the Gear-Generator
repository, not here.

## See also

- [assemblies/02 — Mates from code](02-mates-from-code.md) — walking `MateGroup`, `AddMate5`
- [assemblies/04 — Mates between non-parallel axes](04-mates-between-non-parallel-axes.md) — `CreateTransform` and the `Transform2` put used to restore
- [assemblies/06 — Read every mate](06-read-every-mate.md) — which gear a mate's numerator belongs to, and the whole mate list as data
- [reading/12 — Snapshot suppression before you suppress](../reading/12-snapshot-suppression-before-you-suppress.md)
- [connect/02 — Attach from Python](../connect/02-attach-from-python.md)
- [connect/10 — Driving from outside Windows](../connect/10-driving-from-outside-windows.md)
- [GOTCHAS §1, §10, §55, §73](../../GOTCHAS.md)
- [assemblies/07 — Configurations that hold different positions](07-configurations-that-hold-different-positions.md) — fixing a mechanism at chosen positions instead of dragging
- [assemblies/10 — Mate a gear train that turns](10-mate-a-gear-train-that-turns.md) — the third assembly, and proving a train by a driven mate
- [assemblies/11 — Change a mated gear train](11-change-a-mated-gear-train.md) — what a `Transform2` put does to a mated train
- [GOTCHAS §101](../../GOTCHAS.md) — the drag that did not carry through a gear train
