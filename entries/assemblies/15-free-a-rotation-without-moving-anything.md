---
id: assemblies-15-free-a-rotation-without-moving-anything
title: Replace the mates that hold a component so it can turn, without moving anything
status: verified
verified_on: SolidWorks 2024 SP5 (32.5.0)
language: [python]
api: [IModelDocExtension.SelectByID2, IAssemblyDoc.AddMate5, IFeature.GetSpecificFeature2, IMate2.Type, IMate2.Alignment, IFeature.Select2, IModelDoc2.EditDelete, IModelDoc2.EditRebuild3, IComponent2.Transform2, IFeature.GetErrorCode2, IDimension.GetSystemValue3]
keywords: [coordinate system mate, swMateCOORDINATE, mate type 20, free a rotation, release one degree of freedom, unlock rotation, carrier will not turn, component locked, replace mate, origin to origin coincident, Point1@Origin, EXTSKETCHPOINT, plane coincident, angle mate at current angle, key two parts, keyed, nothing moved, transform snapshot, differential carrier, delete mate]
answers: "A component is held by a mate that fixes all six degrees of freedom (a coordinate-system mate), and it needs to turn about one axis. How do I swap that mate for ones that leave the rotation free, and key another part to it, without anything moving?"
---

# Replace the mates that hold a component so it can turn, without moving anything

## What this is for

A component in an existing assembly is held by one mate that removes every
degree of freedom: a coordinate-system mate (`swMateCOORDINATE`, `IMate2.Type`
20), such as a differential carrier pinned at the assembly origin. The
mechanism needs it to turn about one axis. Deleting the mate first would leave
the component floating and let the solver move it; adding the new mates first
can over-define or shift it. The order below changed the holding mates with
**nothing moving at any step**, checked against a snapshot of every
component's transform, and then keyed a second part to the freed one with an
angle mate at their current angle.

Lengths at the API are **metres** and angles **radians**.

## The calls

From the script that ran, with component and assembly names replaced by
placeholders (`Carrier-1`, `Dog-1`, `Asm1`). The helpers it imports:

```python
def comps(asm):
    return {c.Name2: c for c in asm.GetComponents(True) or ()}


def mates(asm):
    res = {}
    f = asm.FirstFeature
    while f is not None:
        if f.GetTypeName2 == "MateGroup":
            s = f.GetFirstSubFeature
            while s is not None:
                res[s.Name] = s
                s = s.GetNextSubFeature
        f = f.GetNextFeature
    return res


def errors(asm):
    bad = []
    for n, s in mates(asm).items():
        w = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, False)
        code = s.GetErrorCode2(w)
        if code or w.value:
            bad.append((n, code, w.value))
    return bad


def xf(c):
    return [float(v) for v in c.Transform2.ArrayData]


def ang(c):
    a = xf(c)
    return math.atan2(a[1], a[0])


def wrap(x, p=P20):
    x = x % p
    return x - p if x > p / 2 else x
```

`P20` is one tooth of a 20-tooth part, `wrap`'s default; here it is always
given `2 * math.pi`. `CAR` and `DOG` are the two components' `Name2`
(`Carrier-1`, `Dog-1`), `TITLE` the assembly's title without its extension,
`asm` the assembly document.

The steps, each followed by a check that no component moved and no mate
reports an error:

```python
asm.ShowConfiguration2("Default"); asm.EditRebuild3
CFGS = list(asm.GetConfigurationNames)
base = {n: xf(c) for n, c in comps(asm).items()}


def rebuild(): asm.EditRebuild3


def sel(name, kind, append):
    if not ext.SelectByID2(name, kind, 0, 0, 0, append, 1, swcom._null_dispatch(), 0):
        raise SystemExit(f"STOP: could not select {name} ({kind})")


def add_mate(kind, align=2, flip=False, angle=0.0):
    before = set(mates(asm))
    st = out()
    r = call(asm, "AddMate5", kind, align, flip, 0.0, 0.0, 0.0, 1.0, 1.0, angle, angle, angle, False, False, 0, st)
    call(asm, "ClearSelection2", True)
    new = [n for n in mates(asm) if n not in before]
    if len(new) != 1:
        raise SystemExit(f"STOP: AddMate5 type {kind} made {new} (returned {r}, status {st})")
    return mates(asm)[new[0]]


def delete_feat(f):
    call(asm, "ClearSelection2", True); f.Select2(False, 0); asm.EditDelete(); rebuild()


def moved(tol=1e-7):
    now = {n: xf(c) for n, c in comps(asm).items()}
    return {n: round(max(abs(a - b) for a, b in zip(now[n], base[n])), 9) for n in base
            if max(abs(a - b) for a, b in zip(now[n], base[n])) > tol}


def mtype(s): return s.GetSpecificFeature2.Type


# 1. origin on origin: holds the position, leaves every rotation
sel(f"Point1@Origin@{CAR}@{TITLE}", "EXTSKETCHPOINT", False); sel("Point1@Origin", "EXTSKETCHPOINT", True)
m = add_mate(0); rebuild()
print(f"origin-origin coincident -> {m.Name} type {mtype(m)}")
# (the script's fallback for a type-20 result is left out here: it was never reached)
m.Name = "Carrier at Origin"; rebuild()
print("  errors", errors(asm) or "none", "| moved", moved() or "nothing")
# 2. a plane on a plane: keeps the axis, leaves the turn about it
sel(f"Front Plane@{CAR}@{TITLE}", "PLANE", False); sel("Front Plane", "PLANE", True)
m = add_mate(0); rebuild()
print(f"front-front coincident -> {m.Name} type {mtype(m)} align {m.GetSpecificFeature2.Alignment}")
m.Name = "Carrier square to Z"; rebuild()
print("  errors", errors(asm) or "none", "| moved", moved() or "nothing")
if errors(asm) or moved(): raise SystemExit("STOP before deleting Coincident1")
# 3. only now delete the coordinate-system mate
c1 = mates(asm)["Coincident1"]
if mtype(c1) != 20: raise SystemExit("STOP: Coincident1 is not the coordinate mate")
delete_feat(c1)
print("deleted Coincident1 | errors", errors(asm) or "none", "| moved", moved() or "nothing")
```

`ext` is the assembly's `IModelDocExtension`; `out()` a by-reference long;
`swcom._null_dispatch()` a typed null dispatch ([connect/02](../connect/02-attach-from-python.md)).
`"Point1@Origin"` alone is the **assembly's** origin;
`"Point1@Origin@<component>@<assembly>"` a component's
([assemblies/04](04-mates-between-non-parallel-axes.md#selecting-a-components-origin)).
`EditRebuild3` and `GetConfigurationNames` are reached by attribute access,
which runs them; `EditDelete()` returns nothing and must be called
([GOTCHAS §55](../../GOTCHAS.md)).

### Keying a second part to the freed one at its current angle

A part that should turn with the freed one (here a dog ring that only has to
follow the carrier) gets an angle mate between the two parts' Right planes,
**at the angle they already stand at**, so the mate holds their relation
without moving either. The script tries alignments and flips until one moves
nothing:

```python
cs = comps(asm)
rel = wrap(ang(cs[DOG]) - ang(cs[CAR]), 2 * math.pi)
want = abs(rel)
print(f"dog - carrier angle now {math.degrees(rel):.6f} deg")
done = False
for align in (2, 0, 1):
    for flip in (False, True):
        sel(f"Right Plane@{DOG}@{TITLE}", "PLANE", False); sel(f"Right Plane@{CAR}@{TITLE}", "PLANE", True)
        m = add_mate(6, align, flip, want); rebuild()
        cs = comps(asm)
        r2 = wrap(ang(cs[DOG]) - ang(cs[CAR]), 2 * math.pi)
        mv = moved(1e-9)
        print(f"  angle mate align {align} flip {flip}: dog-carrier {math.degrees(r2):.6f} | errors {errors(asm) or 'none'} | moved {mv or 'nothing'}")
        if not mv and not errors(asm):
            m.Name = "LockDog keyed to Carrier"; rebuild(); done = True; break
        delete_feat(m)
        for n, c in comps(asm).items():
            if n in mv: put_xf(c, base[n])
        rebuild()
    if done: break
if not done: raise SystemExit("STOP: no angle mate kept the dog in place")
```

`ang` is the turn of a component's own X axis about the assembly Z, so this
form assumes both parts turn about Z. `put_xf` puts a recorded frame back
through `IMathUtility.CreateTransform` and a `Transform2` put
([assemblies/04](04-mates-between-non-parallel-axes.md#setting-a-components-frame)).

## What happened

- **The origin-to-origin coincident came out a plain coincident**, `Type` 0,
  not a coordinate-system mate: no error, nothing moved. Its entities read
  `ReferenceType2` 25 for the component's origin and 11 for the assembly's.
- **The plane-to-plane coincident**: `Type` 0, `Alignment` 0, no error, nothing
  moved.
- **Deleting the coordinate-system mate** (`Type` 20) after both: no error,
  nothing moved (every one of the sixteen transform numbers of every component
  within 1e-7 of the snapshot).
- **The angle mate at the current angle** was kept at the first combination
  tried, alignment 2 (closest) and `Flip` False, at 77.055592°: nothing moved
  (within 1e-9), no error. Its dimension read back 1.3448738 rad (77.0556°).
- **The freed component then turned.** A drag of the carrier in each
  configuration ([assemblies/05](05-test-motion-with-the-drag-operator.md#a-bevel-differential-and-a-planetary-on-2024))
  turned the parts around it as the configuration's mates said: free side gears
  differentially in the configuration without the lock, everything as one body
  in the configuration with it.
- Read in each of the three configurations afterwards, every component's
  transform matched the snapshot taken before any change to 5.6e-16, and no
  mate reported an error.

The new mates were made with `Default` active and were on in all three
configurations (`IsSuppressed2` read `False` for each).

## Why it is not obvious

- **Delete last.** The order matters only because the snapshot check is
  strict: each new mate was proven harmless before the mate that pinned the
  component went. Deleting first would have left nothing holding the part
  while the next mate solved.
- **"At the current angle" still needs checking.** The same pattern in a top
  assembly, between parts inside two **different flexible sub-assemblies**,
  failed: the first combination (alignment 2, `Flip` False, 48.7091°) moved
  seven components, and each of the other eleven combinations moved nothing but
  left the new angle mate and two existing coincident mates at
  `GetErrorCode2` 51 with the warning flag `True`. Every attempt was deleted
  and the moved components put back. Why it failed there was not found; see
  [assemblies/17](17-flexible-sub-assemblies.md).
- The script feared that a coincident between two origins could come out as a
  coordinate-system mate again, and carried a fallback (a sketch point at the
  component's origin instead). It was never needed.

## What it does not do

- One assembly, one freed component, about one axis (the assembly Z). Freeing
  a rotation about another axis, or a translation, was not tried.
- What `Alignment` and `Flip` mean for an angle mate between planes was not
  studied; the loop simply keeps the first combination that moves nothing.
- The angle test measures turn about Z only; parts turning about other axes
  need another measure.

## Evidence

SolidWorks 2024 SP5 (`RevisionNumber` 32.5.0), 2026-11-16, Python 3.13 with
pywin32 late binding, launched from WSL
([connect/10](../connect/10-driving-from-outside-windows.md)). A bevel
differential sub-assembly with a sliding lock collar, three configurations.
From the run's output, names replaced:

```
active Default | errors none
origin-origin coincident -> Coincident15 type 0
  errors none | moved nothing
front-front coincident -> Coincident16 type 0 align 0
  errors none | moved nothing
deleted Coincident1 | errors none | moved nothing
dog - carrier angle now 77.055592 deg
  angle mate align 2 flip False: dog-carrier 77.055592 | errors none | moved nothing
final errors none | moved nothing
```

The kept mates read back: `Carrier at Origin` type 0, entities
`(Carrier-1, 25), (Asm1, 11)`, error `0, False`; `Carrier square to Z` type 0,
entities `(Carrier-1, 4), (Asm1, 4)`; `LockDog keyed to Carrier` type 6, entities
`(Dog-1, 4), (Carrier-1, 4)`. A comparison of every component's recorded
transform per configuration before the change and after it: "worst 2.776e-17
IDENTICAL (1e-9)", and after the drag tests and their restores "worst
5.551e-16". The failed cross-sub-assembly attempt is from a later run in the
same session.

## See also

- [assemblies/02 — Mates from code](02-mates-from-code.md) — `AddMate5`, deleting and renaming mates
- [assemblies/04 — Mates between non-parallel axes](04-mates-between-non-parallel-axes.md) — selecting a component's origin, and putting a frame
- [assemblies/05 — Test motion with the drag operator](05-test-motion-with-the-drag-operator.md) — the drag that showed the freed rotation
- [assemblies/06 — Read every mate](06-read-every-mate.md) — `IMate2.Type` 20 and the entity types
- [assemblies/16 — Turn a mechanism with a temporary drive](16-turn-a-mechanism-with-a-temporary-drive.md) — the same "at its current angle" mate, used as a drive
- [assemblies/17 — Flexible sub-assemblies](17-flexible-sub-assemblies.md) — where the keying mate failed
- [GOTCHAS §55](../../GOTCHAS.md)
