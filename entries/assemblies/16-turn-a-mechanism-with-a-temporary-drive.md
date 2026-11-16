---
id: assemblies-16-turn-a-mechanism-with-a-temporary-drive
title: Turn a mechanism in an existing assembly with a temporary drive mate, and put every configuration back
status: verified
verified_on: SolidWorks 2024 SP5 (32.5.0)
language: [python]
api: [IAssemblyDoc.AddMate5, IFeature.GetFirstDisplayDimension, IDisplayDimension.GetDimension2, IDimension.GetSystemValue3, IDimension.SetSystemValue3, IModelDoc2.EditRebuild3, IComponent2.Transform2, IModelDoc2.ShowConfiguration2, IModelDoc2.GetConfigurationNames, IModelDoc2.EditDelete, IMathUtility.CreateTransform]
keywords: [drive a mechanism, motion test, temporary angle mate, drive mate, what turns with what, clutch engaged, coupling check, turn a gear train from code, angle mate at current angle, SetSystemValue3 this configuration, restore positions, transform snapshot, positions changed in other configurations, configuration positions spread, re-put per configuration, drag does not carry through gear mate, IDragOperator alternative]
answers: "How do I turn one part of an existing assembly from code and see which other parts follow (does this clutch couple these shafts?), without a drive mate of my own already in it, and put everything back afterwards in every configuration?"
---

# Turn a mechanism with a temporary drive mate, and put every configuration back

## What this is for

An assembly built by someone else: shafts, gears and clutches mated so they
turn, several configurations for the clutch positions. The question is which
parts turn when one does, in each configuration. Moving the part directly
does not answer it: a `Transform2` put turns that part alone
([GOTCHAS §98](../../GOTCHAS.md)), and the drag operator did not carry the
motion through the gear mates of this assembly either
([assemblies/05](05-test-motion-with-the-drag-operator.md#a-bevel-differential-and-a-planetary-on-2024)).
What worked is what [assemblies/10](10-mate-a-gear-train-that-turns.md#one-degree-of-freedom-and-a-drive)
does for a train it built, done temporarily: add an angle mate that holds the
part at the angle it already stands at, change that mate's value so the
**solver** turns the part, read every component's turn, and delete the mate.

The drive changed positions in configurations other than the one it ran in, so
the second half of this entry is recording every configuration first and
putting it back afterwards.

Angles at the API are **radians**, lengths **metres**.

## The drive

From the script that ran, component names replaced by placeholders. `comps`, `mates`, `errors`, `xf` and `put_xf` are the helpers in
[assemblies/15](15-free-a-rotation-without-moving-anything.md#the-calls);
`mat`, `mm` and `tr` build 3×3 rotation matrices from `ArrayData` (rotation by
columns), multiply and transpose them.

```python
K, DRV, DELTA = sys.argv[3], sys.argv[4], float(sys.argv[5])
LAY = "Layout-1"
asm.ShowConfiguration2(K); asm.EditRebuild3
base = {n: xf(c) for n, c in comps(asm).items()}


def turn(a, b):
    D = mm(mat(a), tr(mat(b)))
    return math.degrees(math.atan2(D[1][0], D[0][0])), abs(D[2][2] - 1) < 1e-7, max(abs(a[9 + k] - b[9 + k]) for k in range(3)) * M


def moved(tol=1e-9):
    return {n: c for n, c in comps(asm).items() if max(abs(x - y) for x, y in zip(xf(c), base[n])) > tol}


def delete_feat(f): call(asm, "ClearSelection2", True); f.Select2(False, 0); asm.EditDelete(); asm.EditRebuild3


a0 = base[DRV]; want = abs(math.degrees(math.atan2(a0[1], a0[0]))) % 180.0
if want > 90: want = 180.0 - want  # plane-plane angle in 0..90
print(f"[{K}] drive {DRV}: plane angle now {want:.4f} deg | errors {errors(asm) or 'none'}")
drive = None
for align in (2, 0, 1):
    for flip in (False, True):
        for val in (want, 180.0 - want):
            call(asm, "ClearSelection2", True)
            ok = ext.SelectByID2(f"Right Plane@{DRV}@{TITLE}", "PLANE", 0, 0, 0, False, 1, swcom._null_dispatch(), 0) and \
                ext.SelectByID2(f"Right Plane@{LAY}@{TITLE}", "PLANE", 0, 0, 0, True, 1, swcom._null_dispatch(), 0)
            if not ok: raise SystemExit("STOP: planes did not select")
            prev = set(mates(asm)); st = out()
            call(asm, "AddMate5", 6, align, flip, 0.0, 0.0, 0.0, 1.0, 1.0, math.radians(val), math.radians(val), math.radians(val), False, False, 0, st)
            call(asm, "ClearSelection2", True)
            new = [n for n in mates(asm) if n not in prev]
            if len(new) != 1: continue
            m = mates(asm)[new[0]]; asm.EditRebuild3
            mv = moved()
            if not mv and not errors(asm):
                drive = m; print(f"  drive mate {m.Name}: align {align} flip {flip} value {val:.4f} moved nothing"); break
            delete_feat(m)
            for n, c in moved().items(): put_xf(c, base[n])
            asm.EditRebuild3
        if drive: break
    if drive: break
if drive is None: raise SystemExit("STOP: no drive mate kept everything in place")
dim = drive.GetFirstDisplayDimension.GetDimension2(0)
v0 = dim.GetSystemValue3(1, None)[0]
for sgn in (1, -1):
    r = dim.SetSystemValue3(v0 + sgn * math.radians(DELTA), 1, None); asm.EditRebuild3
    t = turn(xf(comps(asm)[DRV]), base[DRV])[0]
    print(f"  drive value {math.degrees(v0):.4f} -> {math.degrees(v0) + sgn * DELTA:.4f} (set {r}): {DRV} turned {t:.4f}")
    if abs(abs(t) - DELTA) < 1e-3: break
print(f"  after the drive: errors/warnings {errors(asm) or 'none'}")
for n, c in sorted(comps(asm).items()):
    t, pure, sh = turn(xf(c), base[n])
    if abs(t) > 1e-6 or not pure or sh > 1e-6:
        print(f"   {n:34} turned {t:9.4f} deg about world Z{'' if pure else ' (NOT pure Z)'} | shift {sh:.4f} mm")
print("   not moved:", sorted(n for n, c in comps(asm).items() if max(abs(x - y) for x, y in zip(xf(c), base[n])) <= 1e-9))
delete_feat(drive)
```

The arguments are the configuration, the driven component's `Name2` and the
turn in degrees; `ext` is the assembly's `IModelDocExtension`, `TITLE` its
title without the extension, `out()` a by-reference long, `M` 1000.

The drive is between the driven part's Right plane and the fixed layout part's
Right plane, so the angle between the planes is the part's turn about the
assembly Z folded into 0–90°. `GetSystemValue3(1, None)` and
`SetSystemValue3(value, 1, None)` read and set the value in the **active**
configuration only (`1` = `swSetValue_InThisConfiguration`; see
[assemblies/13](13-assembly-configurations-from-code.md#a-dimensions-value-in-this-configuration-or-in-all)).

## What happened

In a planetary gearbox with sliding clutch sleeves and four configurations, the
output dog of one clutch driven 10°:

- **The drive mate moved nothing when it was made**, at the first combination
  tried both times (alignment 2, `Flip` False, the current plane angle:
  51.2887° in one configuration, 61.2887° in another), and no mate reported an
  error.
- **`SetSystemValue3(v0 + 10°, 1, None)` returned 0, and after `EditRebuild3`
  the driven part had turned −10.0000° about the assembly Z** with no shift:
  making the plane angle larger turned it the negative way here. The script
  tries both signs and keeps the one that turned it by the amount asked; read
  the turn rather than assume its sign.
- **What followed differed by configuration, as the clutches said.** In the
  configuration with the second clutch engaged, the dog, its sliding sleeve,
  that sleeve's hub and both chain sprockets turned −10.0000° each, and the
  thirteen other components 0. In the configuration with it disengaged, the
  dog and the two sprockets turned −10.0000° and the sleeve and hub did not.
  The dog drove a sprocket through a 1 : 1 gear mate between the dog's
  reference axis and the sprocket's bore face
  ([assemblies/10](10-mate-a-gear-train-that-turns.md#a-1--1-gear-mate-between-two-components-on-one-axis)).
- **No mate error after the drive, and none after deleting the drive mate.**

On the same assembly the drag operator, dragging the same dog 10° under each
of nine combinations of `TransformType` 0–2 and `DragMode` 0–2, turned the dog
exactly 10.0° and **nothing else**, with no warning
([assemblies/05](05-test-motion-with-the-drag-operator.md#a-bevel-differential-and-a-planetary-on-2024)).

## Putting every configuration back

Deleting the drive mate does not put the parts back, and it was not only the
active configuration that had changed. Record first, then restore and verify,
configuration by configuration:

```python
# record: every component's frame in every configuration
res = {"active": start, "cfg": {}}
for k in asm.GetConfigurationNames:
    asm.ShowConfiguration2(k); asm.EditRebuild3
    cs = comps(asm)
    res["cfg"][k] = {n: xf(c) for n, c in cs.items()}
asm.ShowConfiguration2(start); asm.EditRebuild3
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"xf_{TAG}.json"), "w"), indent=1)
```

```python
# restore: put back what differs, until every configuration matches
def off(k):
    cs = comps(asm)
    return {n: max(abs(a - b) for a, b in zip(xf(cs[n]), rec["cfg"][k][n])) for n in rec["cfg"][k]
            if max(abs(a - b) for a, b in zip(xf(cs[n]), rec["cfg"][k][n])) > 1e-9}


for rnd in range(3):
    for k in rec["cfg"]:
        asm.ShowConfiguration2(k); asm.EditRebuild3
        o = off(k)
        if o:
            cs = comps(asm)
            for n in o: put_xf(cs[n], rec["cfg"][k][n])
            asm.EditRebuild3
            print(f"round {rnd} [{k}] put {sorted(o)} -> still off {off(k) or 'none'} | errors {errors(asm) or 'none'}")
    bad = {}
    for k in rec["cfg"]:
        asm.ShowConfiguration2(k); asm.EditRebuild3
        if off(k) or errors(asm): bad[k] = (off(k), errors(asm))
    print(f"round {rnd} verify:", bad or "all configurations match the record, no mate errors")
    if not bad: break
asm.ShowConfiguration2(rec["active"]); asm.EditRebuild3
```

`comps` is called again after every `ShowConfiguration2` because handles held
across a show go stale ([GOTCHAS §108](../../GOTCHAS.md)).

What it found, after one drive in each of two configurations (each drive mate
deleted at once):

- **Components were off in all four configurations**, not only the two that
  were driven, and including a component (the sun gear) that neither drive
  turned in its own configuration.
- **The first round's puts disturbed the configurations put before them**:
  each configuration read "still off none" straight after its own puts, yet
  the verify pass found three of the four off again. **The second round made
  all four match the record**, with no mate errors.

Earlier the same evening, drags with the drag operator in one configuration
(one of them followed by a `ForceRebuild3(False)`), each undone at once by
puts in that configuration, had left the dragged parts
matching that configuration in **every** configuration: a relative angle
between two parts that had read 236.57°, 287.86°, 236.57° and 91.74° in the
four configurations read 287.86° in all four. One round of the restore fixed
it. See [GOTCHAS §119](../../GOTCHAS.md).

## Why it is not obvious

- **The drive needs no global and no lasting change.** A temporary mate whose
  value starts at the current angle is invisible to the mechanism until the
  value changes, and the assembly's own mates are untouched.
- **The angle between two planes is folded.** Only 0–180° can be given, and
  which side the solver takes depends on alignment and `Flip`; trying
  combinations until one moves nothing is how the script found a drive that
  starts where the part is.
- **Positions in other configurations are not safe.** Whether a configuration
  keeps its own component positions has been seen both ways in this collection
  ([GOTCHAS §83](../../GOTCHAS.md),
  [assemblies/13](13-assembly-configurations-from-code.md#where-components-stand-in-each-configuration)).
  Here the gear mates were on in every configuration, and a solver move in one
  configuration reached the others. Record all of them before driving.

## What it does not do

- Which step moved the other configurations (the drive, the deletion of the
  drive mate, the rebuild after it, or the restoring puts) was not separated.
- Why the first round of puts disturbed configurations already put back is not
  known; the loop simply repeats until a verify pass is clean (two rounds here,
  of at most three).
- Only turns about the assembly Z were driven and measured.
- The drive was tried on one assembly; the drag-operator comparison is on the
  same one.

## Evidence

SolidWorks 2024 SP5 (`RevisionNumber` 32.5.0), 2026-11-16, Python 3.13 with
pywin32 late binding, launched from WSL. A planetary gearbox assembly of
eighteen top-level components and 41 entries under its `MateGroup`, with four configurations for its
clutch positions. From the output, names replaced:

```
[C2] drive Dog-1: plane angle now 51.2887 deg | errors none
  drive mate Angle1: align 2 flip False value 51.2887 moved nothing
  drive value 51.2887 -> 61.2887 (set 0): Dog-1 turned -10.0000
  after the drive: errors/warnings none
   Dog-1          turned  -10.0000 deg about world Z | shift 0.0000 mm
   Sleeve-2       turned  -10.0000 deg about world Z | shift 0.0000 mm
   Hub-2          turned  -10.0000 deg about world Z | shift 0.0000 mm
   SprocketA-1    turned  -10.0000 deg about world Z | shift 0.0000 mm
   SprocketB-3    turned  -10.0000 deg about world Z | shift 0.0000 mm
drive deleted: yes | errors none
[C1] drive Dog-1: plane angle now 61.2887 deg | errors none
  drive mate Angle1: align 2 flip False value 61.2887 moved nothing
  drive value 61.2887 -> 71.2887 (set 0): Dog-1 turned -10.0000
   Dog-1          turned  -10.0000 deg about world Z | shift 0.0000 mm
   SprocketA-1    turned  -10.0000 deg about world Z | shift 0.0000 mm
   SprocketB-3    turned  -10.0000 deg about world Z | shift 0.0000 mm
drive deleted: yes | errors none
round 0 [C1] put ['Dog-1', 'Sun-1', 'SprocketA-1', 'SprocketB-3'] -> still off none | errors none
round 0 [C2] put ['Dog-1', 'Hub-2', 'Sleeve-2', 'SprocketA-1', 'SprocketB-3', 'Sun-1'] -> still off none | errors none
round 0 [C3] put ['Dog-1', 'Sun-1'] -> still off none | errors none
round 0 [C4] put ['Dog-1', 'Sun-1'] -> still off none | errors none
round 0 verify: {'C1': (...), 'C2': (...), 'C3': (...)}
round 1 [C1] put ['Dog-1', 'Sun-1'] -> still off none | errors none
round 1 [C2] put ['Dog-1', 'Sun-1'] -> still off none | errors none
round 1 [C3] put ['Dog-1', 'Sun-1'] -> still off none | errors none
round 1 verify: all configurations match the record, no mate errors
```

(The round-0 verify listed, per configuration, the dog and the sun gear off by
up to 1.82 in their `ArrayData` entries.) The relative-angle readings after the
drags are from the record script, before and after them: `236.572769`,
`287.861518`, `236.572769`, `91.741628` degrees, then `287.861518` four times.

## See also

- [assemblies/05 — Test motion with the drag operator](05-test-motion-with-the-drag-operator.md) — the drag on this assembly, and on a differential where it did carry
- [assemblies/10 — Mate a gear train that turns](10-mate-a-gear-train-that-turns.md#one-degree-of-freedom-and-a-drive) — a permanent drive linked to a global
- [assemblies/13 — Assembly configurations from code](13-assembly-configurations-from-code.md) — values per configuration, and where components stand in each
- [assemblies/15 — Free a rotation without moving anything](15-free-a-rotation-without-moving-anything.md) — the "at its current angle" mate, kept
- [assemblies/04 — Mates between non-parallel axes](04-mates-between-non-parallel-axes.md#setting-a-components-frame) — the `Transform2` put behind `put_xf`
- [GOTCHAS §83, §98, §108, §119](../../GOTCHAS.md)
