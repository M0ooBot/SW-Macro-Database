---
schema: 2
id: assemblies-07-configurations-that-hold-different-positions
title: Make assembly configurations that each hold a mechanism in a different position
answers: "How do I make configurations of an assembly that each put a mechanism in a different position, so switching configuration moves it and each position is exact?"
keywords: [configuration, positions, motion positions, end of stroke, mechanism position, configuration specific mate, suppress mate in configuration, SetSuppression2, swInConfigurationOpts_e, IsSuppressed2, AddConfiguration2, positions not per configuration, configuration shows wrong position, over defined, AddMate5 error 5, mate error 51, limit mate, extreme distance, point coincident mate, assembly sketch point, exact point, rounding, limit mate entities, anti-aligned coincident, mate with no entities, stale reference, server threw an exception, -2147417851, ShowConfiguration2 raises, suppress component in one configuration]
api: [IConfigurationManager.AddConfiguration2, IModelDoc2.ShowConfiguration2, IModelDoc2.GetConfigurationNames, IAssemblyDoc.AddMate5, IFeature.SetSuppression2, IFeature.IsSuppressed2, IFeature.IsSuppressed, IFeature.GetErrorCode2, ISketchManager.InsertSketch, ISketchManager.CreatePoint, ISketchManager.AddToDB, ISketch.GetSketchPoints2, IModelDoc2.BlankSketch, IMate2.MateEntity, IMateEntity2.Reference, IMateEntity2.EntityParams, IComponent2.SetSuppression2, IModelDocExtension.DeleteSelection2]
language: [python]
status: verified
verified_on: SolidWorks 2024 SP5 (32.5.0)
majors: [32]
evidence: []
recipe_status: null
recipe_evidence: []
superseded_by: null
---

# Make assembly configurations that each hold a mechanism in a different position

## What this is for

A mechanism shown at several positions — the two ends of a stroke, a midpoint —
each as a configuration, for a drawing that overlays them
([drawings/06](../drawings/06-alternate-position-views.md)) or for checking
clearances at each. It looks like "add a configuration, drag the part, save". It
was not, here, because **the dragged positions were not kept per
configuration** (but see the qualification below: a later measurement with a
`Transform2` put found positions kept per configuration).

Attach as in [assemblies/06](06-read-every-mate.md#attaching).

## Why dragging is not enough

A configuration stores which mates and components are suppressed, not where the
free components are. Whatever the mates leave free sits where it was last
solved, in *every* configuration. Switching to a configuration with no extra
mates leaves the mechanism wherever the previous one put it. So each
configuration needs **its own mates that fix the position completely**, active
only in that configuration.

**Qualified since.** The drag observation behind that paragraph records
neither how the positions were set nor how they were read. The instrumented
reads further down (show, then `ForceRebuild3(False)`) are of mates per
configuration, and the table's "showed the same position" is of an attempt
whose mates were in error (51). A later measurement on SolidWorks 2026 (34.1.1)
and 2024 SP5 found positions kept per configuration under another procedure: a
component held by an axis mate and a distance along it, with no gear mate,
turned by a `Transform2` put and a top-only rebuild (`ForceRebuild3(True)`),
kept a different turn in each configuration, through a save and reopen, read
through freshly fetched handles ([assemblies/13](13-assembly-configurations-from-code.md#where-components-stand-in-each-configuration)).
Not tried there, so the two are not reconciled: a drag instead of a put; a full rebuild (`ForceRebuild3(False)`) after a show; a put on a component whose gear mate is on in every configuration; a component free to slide as well as turn. The recipe
below, mates per configuration, holds either way.

## Mates that hold one exact position

The mates must have **one** solution with the assembly's other mates, and must
not fight them:

| Tried | Result |
|---|---|
| Distance from the moving pin to a plane, plus distance from pin to the slot wall | Added with error 5; four existing concentric/coincident mates went to error 51; both configurations showed the same position |
| A second limit distance mate per configuration | Added with error 5 in one configuration; that mate in error 51 |
| A point-to-point coincident on a point a hundredth of a millimetre off the pin's circle | Added with error 5, mates in error 51 |
| **Pin axis coincident with an exact point in a hidden assembly sketch**, plus one distance mate where the mechanism has play | Added cleanly (1); every configuration solved with no mate errors |

So: put the target positions as **points in an assembly sketch**, computed
exactly (not rounded for display), mate the moving axis to the point, and add a
distance mate only for the degree of freedom the point leaves (a slider with
play). An existing **limit** mate that already bounds the travel stays; the
equality mates sit inside its range.

```python
call(asm, "ClearSelection2", True); asm.FeatureByName("Front Plane").Select2(False, 0)
sm.InsertSketch(True); sm.AddToDB = True
pts = {cfg: sm.CreatePoint(x / 1000, y / 1000, 0) for cfg, (x, y) in POINTS.items()}
sm.AddToDB = False; sm.InsertSketch(True)
```

`CreatePoint` takes **metres** in the sketch's plane. Find the point again by its
coordinates, select the moving axis and the point at mark 1, and add a coincident
mate (`AddMate5` type 0):

```python
sk = call(sk_feat, "GetSpecificFeature2")
spts = list(call(sk, "GetSketchPoints2") or [])
def find_pt(x, y):
    return next(p for p in spts if abs(call(p, "X") * 1000 - x) < 0.01 and abs(call(p, "Y") * 1000 - y) < 0.01)
for cfg, (x, y) in POINTS.items():
    asm.ShowConfiguration2(cfg); asm.ForceRebuild3(False)
    sd = call(selmgr, "CreateSelectData"); sd.Mark = 1; sd2 = call(selmgr, "CreateSelectData"); sd2.Mark = 1
    call(asm, "ClearSelection2", True); call(lim().MateEntity(0), "Reference").Select4(False, sd); find_pt(x, y).Select4(True, sd2)
    err = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    asm.AddMate5(0, 2, False, 0, 0, 0, 1, 1, 0, 0, 0, False, False, 0, err); call(asm, "ClearSelection2", True); asm.ForceRebuild3(False)
```

Here the pin's axis came from an existing mate (`MateEntity(0).Reference`); any
way of selecting the axis will do. Hide the helper sketch afterwards with
`BlankSketch` on the selected sketch feature.

## One configuration's mates, suppressed everywhere else

`AddConfiguration2(name, comment, "", 0, "", "", True)` adds and activates a
configuration. Then, for each new mate, `IFeature.SetSuppression2(0, 3, names)`
suppresses it (`0`) in the **listed** configurations (`3`):

```python
c = cm.AddConfiguration2(cfg, "End of travel", "", 0, "", "", True)
asm.FeatureByName(nm).SetSuppression2(0, 3, VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_BSTR, [n for n in names if n != cfg]))
```

Read the result back for every configuration at once with
`IsSuppressed2(3, names)`, which returns one flag per name:

```python
st = list(s.IsSuppressed2(3, VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_BSTR, CFGS)))
```

A mate added while a configuration is active can come out suppressed in that
configuration and live in the others — the inverse of what was meant; this check
catches it. (That was seen once, on a mate made by hand. Measured since with
`AddMate5`, on SolidWorks 2026 and 2024 SP5: a mate made while a non-template
configuration was active came out **suppressed in the template's `Default`
and on in the others**, the active one included
([assemblies/13](13-assembly-configurations-from-code.md#adding-showing-and-deleting)).
Either way, set and read back every flag.)

## Checking the positions

Switch through the configurations in an order that revisits each, rebuild, and
read where the moving parts are and whether any mate is in error:

```python
for cfg in ("Position A", "Position B", "Position A", "Default", "Position B", "Position A", "Position B"):
    asm.ShowConfiguration2(cfg); asm.ForceRebuild3(False)
    px, fx, errs = state(); fol[cfg] = fx; print(f"  {cfg:15} pin x={px:7.2f} slider x={fx:7.2f} errors {errs or 'none'}")
```

where `state()` reads the pin's `EntityParams` (assembly metres,
[assemblies/06](06-read-every-mate.md)), the moving component's box, and every
unsuppressed mate's `GetErrorCode2`. Note what `Default` shows: with no mates of
its own it keeps the last configuration's position.

## A slider: mate the limit mate's own two faces

For a part that only slides (one degree of freedom, bounded by a limit distance
mate), a sketch point was not needed. The limit mate's two entities, re-mated
with an exact value, held each end of the travel: a distance mate for one end,
and a coincident mate, **anti-aligned** (alignment `1`), for the end where the
faces touch. Both added with out code 1 and solved in every configuration.

```python
def add_mate(kind, align, dist, on, cfgs):
    show(asm, on[0])
    limm = call(mates()["LimitDistance1"], "GetSpecificFeature2"); ents = [call(limm, "MateEntity", i) for i in range(2)]
    before = set(mates()); call(asm, "ClearSelection2", True)
    for i, e in enumerate(ents):
        sd = call(selmgr, "CreateSelectData"); sd.Mark = 1; call(e, "Reference").Select4(i > 0, sd)
    if selmgr.GetSelectedObjectCount2(-1) != 2: print("ABORT selection"); return None
    err = z(); asm.AddMate5(kind, align, False, dist / 1000, dist / 1000, dist / 1000, 1, 1, 0, 0, 0, False, False, 0, err)
    call(asm, "ClearSelection2", True)
    new = [n for n in mates() if n not in before]; f = mates()[new[0]]
    print(f"  mate {new} add err={err.value} ents={ents_ok(f)}")
    f.SetSuppression2(0, 3, VA([c for c in cfgs if c not in on], pythoncom.VT_BSTR)); f.SetSuppression2(1, 3, VA(on, pythoncom.VT_BSTR))
    print("   suppressed:", dict(zip(cfgs, list(f.IsSuppressed2(3, VA(cfgs, pythoncom.VT_BSTR))))))
    return new[0]
add_mate(5, 1, 1.5, ["Position A", "Exploded"], CFGS)
add_mate(0, 1, 0.0, ["Position B"], CFGS)
```

`mates()` maps each mate's name to its sub-feature under the `MateGroup`;
`ents_ok` reads each `MateEntity(i).ReferenceComponent.Name2`; `VA` builds a
typed `VARIANT` array; `show` is below. Distances are **metres** in `AddMate5`.

### Read the entities after switching configuration

The first version read the limit mate's entities **once**, then switched
configuration before selecting them. `AddMate5` still returned out code 1, but
the new mate had **no entities** (`ReferenceComponent` was `None` for both) and
read `GetErrorCode2` 51 in its configuration. Selecting it to delete it,
whether through `IFeature.Select2` or `SelectByID2(…, "MATE", …)`, raised "The
server threw an exception" (−2147417851). From a configuration in which the
mate was **suppressed**, `IFeature.Select2(False, 0)` worked and
`IModelDocExtension.DeleteSelection2(3)` removed it. Read the entities inside
`add_mate`, after the switch, as above.

### `ShowConfiguration2` and `ForceRebuild3` can raise and still succeed

On the same assembly, `ShowConfiguration2` and the `ForceRebuild3` after it
raised −2147417851 on some switches. The configuration had changed regardless,
and nothing was left broken. This wrapper trusted the active configuration's
name rather than the call:

```python
def show(doc, cfg):
    cm = call(doc, "ConfigurationManager")
    try: doc.ShowConfiguration2(cfg)
    except Exception: pass
    act = call(call(cm, "ActiveConfiguration"), "Name")
    assert act == cfg, f"config switch failed: wanted {cfg}, active {act}"
    try: doc.ForceRebuild3(False)
    except Exception as e: print(f"    (rebuild in {cfg} raised: {str(e)[:40]})")
```

## Components suppressed in one configuration only

With a configuration active, `IComponent2.SetSuppression2(0)` on eleven
components suppressed them **in that configuration only**: it read 11
suppressed there and 0 in the other three. The call returned 2 each time; what
that value means was not looked up. A drawing view or BOM of that configuration
then left those parts out
([drawings/02](../drawings/02-bom-table-and-balloons.md#a-bom-for-one-configuration-of-a-multi-configuration-assembly)).

## What it does not do

- **Positions from a motion study** were not tried.
- **Dragging into place first, then adding mates**, was not used: a
  `Transform2` put did not stay ([GOTCHAS §73](../../GOTCHAS.md)).
- **Open:** whether the mate suppressed in its own configuration came from
  `AddMate5` while that configuration was active or from a later hand edit. It
  was seen once, made by hand in the UI. `AddMate5` in another assembly did
  something else (above).
- **Open:** how the per-configuration position measured with a put
  ([assemblies/13](13-assembly-configurations-from-code.md#where-components-stand-in-each-configuration))
  meets this entry's drag observation. Not tried: a drag instead of a put; a full rebuild (`ForceRebuild3(False)`) after a show; a put on a component whose gear mate is on in every configuration; a component free to slide as well as turn.

## Evidence

SolidWorks 2024 SP5 (`RevisionNumber` 32.5.0), 2026-10-30, a slider-crank-like
mechanism with a limit distance mate on the slider. Plane-distance mates per
configuration: add errors 5 and 1/5, both configurations then read the same pin
position with four mates at error 51, and the measured travel came out negative
and short. Point mates: `pin-to-point mate err 1` for both, and a seven-switch
test read the two pin and slider positions alternately, each repeat identical to
0.01 mm, with no errors, the travel within 0.01 mm of the design value. A third
point rounded to 0.01 mm added with result 5 and mates at error 51; on the exact
point it solved. Final check over four configurations: every configuration's
mates `IsSuppressed2` matched (own `-`, others `X`), the pin at 0°, 180° and an
intermediate angle, each exactly on the crank radius, the travel equal to the
design value, no mate errors.
Names are placeholders here.

Later run, SolidWorks 2024 SP5 (32.5.0), 2026-11-15, a sliding part bounded by a
limit distance mate, four configurations:

- A distance mate and an anti-aligned coincident on the limit mate's own
  entities added with out code 1; the part read its two end positions in
  alternating switches, with no mate errors.
- Entities read before a switch gave a mate with no entities, error 51, and
  selections that raised −2147417851. Deleting it from a configuration where
  it was suppressed worked.
- `ShowConfiguration2` raised on several switches while `ActiveConfiguration`
  read the requested name.
- `SetSuppression2(0)` on 11 components: 11 suppressed in the active
  configuration, 0 in the others.

## See also

- [assemblies/14 — An in-context part in several configurations](14-in-context-part-across-configurations.md) — a part whose size follows the mechanism

- [assemblies/02 — Mates from code](02-mates-from-code.md) — `AddMate5`
- [assemblies/05 — Test motion with the drag operator](05-test-motion-with-the-drag-operator.md) — whether it can move at all
- [assemblies/06 — Read every mate](06-read-every-mate.md) — `EntityParams`, `GetErrorCode2`, limit mates
- [drawings/06 — Alternate position views](../drawings/06-alternate-position-views.md) — drawing the positions
- [files/02 — Explode configurations](../files/02-explode-configurations.md) — configurations of a part
- [assemblies/13 — Assembly configurations from code](13-assembly-configurations-from-code.md) — the calls in detail, stale handles, per-configuration values, and positions under a put
- [GOTCHAS §23, §73, §83](../../GOTCHAS.md)
