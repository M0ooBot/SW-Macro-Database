---
schema: 2
id: assemblies-06-read-every-mate
title: Read every mate in an assembly, with its entities, gear ratio and folder
answers: "How do I read every mate in an existing assembly — its type, the components and faces it joins, a gear mate's ratio, and which folder it is in?"
keywords: [read mates, list mates, dump mates, mate inventory, existing mates, MateGroup, MateGearDim, MateConcentric, MateCoincident, MateCoordinate, MateDistanceDim, MateLimitDistanceDim, gear mate ratio, GearRatioNumerator, GearRatioDenominator, which gear is the numerator, swMateType_e, swSelectType_e, ReferenceType2, EntityParams, mate folder, FtrFolder, ___EndTag___, limit mate range, MaximumVariation, suppressed mates, mechanism from mates]
api: [IFeatureManager.InsertFeatureTreeFolder2, IFeature.GetFirstSubFeature, IFeature.GetNextSubFeature, IFeature.GetTypeName2, IFeature.GetSpecificFeature2, IFeature.GetDefinition, IFeature.IsSuppressed, IFeature.GetErrorCode2, IMate2.Type, IMate2.Alignment, IMate2.Flipped, IMate2.MaximumVariation, IMate2.MinimumVariation, IMate2.GetMateEntityCount, IMate2.MateEntity, IMateEntity2.ReferenceComponent, IMateEntity2.ReferenceType2, IMateEntity2.EntityParams, IGearMateFeatureData.GearRatioNumerator, IGearMateFeatureData.GearRatioDenominator, IGearMateFeatureData.Reverse, IDistanceMateFeatureData.Distance, IDistanceMateFeatureData.MateAlignment]
language: [python]
status: verified
verified_on: SolidWorks 2024 SP5 (32.5.0); the MateEntity order of code-made mates and code-made mate folders also SolidWorks 2026 (34.1.1)
majors: [32]
evidence: []
recipe_status: null
recipe_evidence: []
superseded_by: null
---

# Read every mate in an assembly

## What this is for

You have an assembly someone else built, and you want its mechanism as data:
which components each mate joins, on which axis, with what gear ratio, which
mates are suppressed, and how they were grouped into folders (often the
grouping *is* the documentation, e.g. "suppress these for this mode"). This
entry is a read-only walk that ran over an existing assembly with several
sub-assemblies, over a hundred mate records and a few dozen gear mates, and
wrote it all to JSON, plus the four things about the result that are easy to
misread.

The full program is [`code/python/dump_mates.py`](../../code/python/dump_mates.py)
(about 260 lines). It also records components and their `Transform2`,
configurations and equations, and walks every sub-assembly once.

## Attaching

`swcom.connect()` refuses anything older than 2026; this ran on 2024 SP5, so it
picks from `find_candidates()` itself. See
[connect/05](../connect/05-choosing-among-versions.md#the-floor-belongs-to-the-application-not-to-swcom).

```python
    candidates = swcom.find_candidates()
    if not candidates:
        print("No running SolidWorks found in the Running Object Table")
        return 3
    app = sorted(candidates, key=lambda c: (c.has_active_doc, c.revision), reverse=True)[0].app
```

## The walk

Mates are the sub-features of the top-level feature whose `GetTypeName2` is
`MateGroup`. Step them with `GetNextSubFeature`, not `GetNextFeature`
(the ledger's `IFeature` rows).

```python
def _sub_features(feature):
    child = _try(feature, "GetFirstSubFeature")
    while child is not None:
        yield child
        child = _try(child, "GetNextSubFeature")


def _mates(doc):
    out = []
    for f in _top_features(doc):
        if _try(f, "GetTypeName2") != "MateGroup":
            continue

        def walk(parent, path):
            for child in _sub_features(parent):
                t = _try(child, "GetTypeName2")
                if t == "FtrFolder":
                    out.append({"name": _plain(_try(child, "Name")), "type_name": t, "folder_path": path})
                    walk(child, path + [_try(child, "Name")])
                else:
                    out.append(_mate(child, path))

        walk(f, [])
    return out
```

The recursion into a folder is in the code as it ran, and it **found nothing**:
every record came back with an empty `folder_path`. See
[Folders](#folders-are-markers-not-parents) for what to do instead.

`_try` is `call` from `swcom` inside a `try` that returns `None`, so a member a
mate type does not have is skipped rather than fatal.

## One mate

```python
def _entity(me):
    comp = _try(me, "ReferenceComponent")
    return {
        "component": _plain(_try(comp, "Name2")) if comp is not None else None,
        "reference_type": _plain(_try(me, "ReferenceType2")),
        # assembly coords, metres: point(0-2), direction(3-5), radius(6)
        "entity_params": _plain(_try(me, "EntityParams")),
    }


def _mate(feature, path):
    rec = {
        "name": _plain(_try(feature, "Name")),
        "type_name": _plain(_try(feature, "GetTypeName2")),
        "folder_path": path,
        "suppressed": _plain(_try(feature, "IsSuppressed")),
    }
    try:
        flag = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, False)
        rec["error_code"] = _plain(feature.GetErrorCode2(flag))
    except Exception:
        rec["error_code"] = None
    mate = _try(feature, "GetSpecificFeature2")
    if mate is not None:
        rec["imate"] = {k: _plain(_try(mate, k)) for k in IMATE_FIELDS}
        n = _try(mate, "GetMateEntityCount")
        ents = []
        for i in range(int(n) if isinstance(n, int) else 0):
            me = _try(mate, "MateEntity", i)
            if me is not None:
                ents.append(_entity(me))
        rec["entities"] = ents
    definition = _try(feature, "GetDefinition")
    if definition is not None:
        data = {}
        for k in DEFINITION_FIELDS:
            v = _try(definition, k)
            if v is not None and not callable(v):
                data[k] = _plain(v)
        rec["definition"] = data
    rec["dimensions"] = _dimensions(feature)
    return rec
```

`IMATE_FIELDS` is `Type`, `Alignment`, `Flipped`, `MaximumVariation`,
`MinimumVariation`, read on the `IMate2` from `GetSpecificFeature2`.
`DEFINITION_FIELDS` is a list of names tried on whatever `GetDefinition`
returns; only those that answered are kept (next section).

## What came back

Type names, `IMate2.Type`, and what the definition answered, on 2024 SP5.
`Type` decoded with `swMateType_e` read from `SolidWorks.Interop.swconst.dll`:

| `GetTypeName2` | `IMate2.Type` | Definition answered |
|---|---|---|
| `MateConcentric` | 1 `swMateCONCENTRIC` | `MateAlignment` |
| `MateCoincident` | 0 `swMateCOINCIDENT` | `MateAlignment` |
| `MateGearDim` | 10 `swMateGEAR` | `GearRatioNumerator`, `GearRatioDenominator`, `Reverse` |
| `MateCoordinate` | 20 `swMateCOORDINATE` | nothing |
| `MateLimitDistanceDim` | 5 `swMateDISTANCE` | `Distance`, `MateAlignment` |
| `MateDistanceDim` | 5 `swMateDISTANCE` | `Distance`, `MateAlignment` |
| `FtrFolder` | (no `IMate2`) | — |

- **A gear mate is `MateGearDim`, not `MateGear`.** Filter on the real string.
- **A limit distance mate has the same `IMate2.Type` as a plain one (5).** Tell
  them apart by `GetTypeName2`. Its range came back on `IMate2`, in metres,
  as offsets from `Distance`: one read `Distance` 0 with a positive
  `MaximumVariation` and `MinimumVariation` 0; another read `Distance` *d* with
  `MaximumVariation` 0 and `MinimumVariation` −*d*. Distance plus each variation
  gives the range. That reading of the two fields is an inference from a
  handful of mates.
- **Do not trust `IDistanceMateFeatureData.MateAlignment` on a plain distance
  mate.** It read 7602281, while `IMate2.Alignment` on the same mate read 2.
- `IGearMateFeatureData` and `IDistanceMateFeatureData` are the interfaces
  those members sit on in `SolidWorks.Interop.sldworks.dll`; the walk reached
  them late-bound and never named them. There is no
  `ILimitDistanceMateFeatureData` in that assembly.
- `ReferenceType2`, decoded with `swSelectType_e`: gear mate entities were
  1 `swSelEDGES` or 2 `swSelFACES`; a coordinate mate's two were
  25 `swSelEXTSKETCHPOINTS` (a sub-assembly) and 11 `swSelSKETCHPOINTS` (the
  assembly's own, `ReferenceComponent` naming the top assembly).
- `EntityParams` is in assembly coordinates, metres: 0–2 a point, 3–5 the
  direction, 6 the radius. Also eight values with 0 radius on a coordinate mate.

## Which gear the numerator belongs to

**`GearRatioNumerator` goes with the *second* entity `MateEntity` lists, the
denominator with the first.** Ratios are stored as the diameters typed, in
metres. On the ring and pinion mate drag-tested in
[assemblies/05](05-test-motion-with-the-drag-operator.md), `MateEntity(0)` was
the pinion and `MateEntity(1)` the ring gear, and the larger number was the
numerator. Dragging the ring turned the pinion numerator / denominator times as
far, so the numerator is the ring's. Every other gear mate in the assembly
where the two sizes differ fits the same rule, in both listing orders: a pair
listed (small, large) had the large diameter as numerator, and the same kind of
pair listed (large, small) had the small one.

So for "how fast does entity *i* turn": entity 0 turns at
numerator / denominator times entity 1, and `Reverse` says whether in the same
sense.

Whether `MateEntity` order is the order the mate was picked in the UI was
**not checked**. Read the order from `MateEntity`, never from the mate's name.

**For mates made from code, the order was measured** (Gear-Generator probe tier
8, SolidWorks 2026 34.1.1 and 2024 SP5 32.5.0, see
[assemblies/10](10-mate-a-gear-train-that-turns.md)). It follows the selection
order for some mate types and not for others:

- **Gear mates: `MateEntity(0)` was the first-selected entity** in all 22 made
  by `AddMate5` (axes, faces, or one of each; a ring selected first or second),
  and `GearRatioNumerator` read back the **second** selection's count. So the
  rule above holds for code-made gear mates too, and the numerator passed to
  `AddMate5` (the first selection's) comes back as the denominator.
- **Point-to-plane distance mates:** `MateEntity(0)` was the first-selected
  (the component's origin point, `ReferenceType2` 25), the plane second (4).
- **Axis-to-axis coincident, face-to-axis concentric and point-to-plane
  coincident mates:** `MateEntity(0)` was the **second**-selected entity (the
  skeleton part's axis or plane, `ReferenceType2` 5 or 4), in every case, on
  both versions.

So do not assume selection order in general; read it per mate. A lock mate's
two entities were whole components (`ReferenceType2` 0) and its type name is
`MateLock`.

## The ratio is not the geometry

**The ratio is what was typed, not the size of what was picked.** Read it from
`GetDefinition`; do not work it out from `EntityParams`' radius:

- An internal gear's picked face was about a third larger across than the
  diameter its gear mates gave.
- A ring and pinion pair picked two faces of nearly the same size, at a ratio
  of about 4 : 1.
- "Gear" mates used as 1 : 1 couplers joined faces of quite different sizes.

## Folders are markers, not parents

Inside a `MateGroup`, a folder does not hold its mates. The walk returns them as
**siblings**, between an `FtrFolder` that opens the folder and an `FtrFolder`
end tag that closes it:

```text
FtrFolder              Group A
FtrFolder              Group A1
MateLimitDistanceDim   LimitDistance1
MateGearDim            GearMate1
...
FtrFolder              Folder3___EndTag___
...
FtrFolder              Group A2
MateGearDim            GearMate5
FtrFolder              Group A2a
MateGearDim            GearMate7
FtrFolder              Folder1___EndTag___
FtrFolder              Folder5___EndTag___
MateGearDim            GearMate9
FtrFolder              Folder7___EndTag___
```

The user's folder and mate names are replaced here; the order, the types and
the end tag names are as returned.

This is [GOTCHAS §19](../../GOTCHAS.md) (a folder is two features) inside the
mate group. Nesting is a stack. This function, run on the recorded order of
that sub-assembly's records, put `GearMate7` three folders deep
(`Group A / Group A2 / Group A2a` above) and ended with the stack empty:

```python
def folder_paths(records):
    """Which folder each mate sits in, from the order the MateGroup listed them."""
    stack, out = [], []
    for r in records:
        if r["type_name"] == "FtrFolder":
            if "___EndTag___" in r["name"]:
                stack.pop()
            else:
                stack.append(r["name"])
            continue
        out.append((r["name"], list(stack)))
    assert not stack, stack
    return out
```

End tags are named after the folder's *first* automatic name, so they do not
match the folder they close (`Folder3___EndTag___` closed `Group A1`), and
the same tag name occurred twice in one assembly (`Folder1___EndTag___`).
Match by position, never by name. Testing the name for `___EndTag___` worked
here, but §19 records a tag renamed `…___EndTag___0` on reopening and a
sturdier test through `IFeatureFolder.GetFeatures`; that test has **not been
run on mate folders**.

**A mate folder made from code behaves the same** (Gear-Generator probe
`mate_folders`, SolidWorks 2026 34.1.1 and 2024 SP5, fresh sessions). Two mates
selected by `IFeature.Select2` (the second appended) and
`IFeatureManager.InsertFeatureTreeFolder2(2)` (`swFeatureTreeFolder_Containing`,
read from `swconst.tlb`; 1 is `EmptyBefore`, 3 `Mold`) made a folder in the
`MateGroup` (`GetTypeName2` `FtrFolder`), which took a new name by an
`IFeature.Name` put. The walk then listed the folder, the two mates as the
**following siblings**, and an end marker `Folder1___EndTag___` (also
`FtrFolder`; named after the folder's first automatic name, not its new one);
the folder's own `GetFirstSubFeature` gave nothing. `IModelDoc2.FeatureByName`
found both mates inside the folder, no mate reported an error, and a walk that
keeps only type names starting with `Mate` skipped both folder entries and still
saw every mate.

A second run walked four cases on both versions (`mate_folders`, runs
20261114-105135 and 20261114-111150, fresh sessions): the one folder; a folder
made inside it the same way, holding one of the two mates; the assembly saved
under its own name, closed and reopened; and the outer folder suppressed.

- **In all four, the mates were ordinary siblings in the `MateGroup` walk and
  `IModelDoc2.FeatureByName` found them.** Every folder entry, each folder and
  each `…___EndTag___` marker, read `GetTypeName2` `FtrFolder`.
- **Nested, and again after the reopen, the walk read:** the outer folder, its
  mate, the inner folder, its mate, `Folder2___EndTag___`, then
  `Folder1___EndTag___`. The inner folder's tag comes first, so the stack in
  `folder_paths` above unwinds correctly. After this reopen the tags kept their
  names, with no `…___EndTag___0` suffix: the renaming §19 records on reopening
  a part was not seen here, which does not show it cannot happen.
- **Suppressing the folder suppresses its mates.** `IFeature.SetSuppression2(0, 1, None)`
  on the outer folder's feature (the call that suppresses a mate) left both
  mates inside reading `IsSuppressed2` `True`, and the walk still listed them;
  `SetSuppression2(1, 1, None)` on the folder brought both back with no mate
  error. So read `IsSuppressed2` on each mate: a mate can be suppressed by its
  folder.
- **Not probed:** unsuppressing a mate on its own while its folder is
  suppressed, and a folder made in the user interface.

## What it does not do

- **Reads only the active configuration.** `IsSuppressed` is this
  configuration's state. Reading another means activating it, which this
  read-only tool does not do.
- **Limit values for angle mates, and `IDistanceMateFeatureData`'s
  `MaximumDistance` / `MinimumDistance`**, were not read. The limit range above
  came from `IMate2` instead.
- **Width, rack-and-pinion, screw, cam and hinge mates did not occur**, so the
  names `DEFINITION_FIELDS` tries for them are untested.
- **Open:** whether `MateEntity` order follows UI pick order. Settle it by
  making a two-gear mate by hand, picking the smaller gear first, and reading
  it back. For mates made by `AddMate5` it is answered above: selection order
  for gear and distance mates, not for coincident and concentric ones.

## Evidence

SolidWorks 2024 SP5 (`RevisionNumber` 32.5.0), 2026-10-28. The program ran
read-only over an open assembly with several sub-assemblies: over a hundred
mate records, including folder markers and a few dozen gear mates; written to
JSON, every field above taken from that file. The gear rule was checked against
every gear mate in it and against the drag result recorded in assemblies/05
(same assembly, same version). `swMateType_e`, `swSelectType_e` and the feature-data interface names
were read by reflection from the `SolidWorks.Interop.sldworks.dll` and
`swconst.dll` installed beside SolidWorks. `folder_paths` ran on the recorded
order, not live.
- Mate folders made by code, again, by the gear-train runner ([`code/python/gear_train/`](../../code/python/gear_train/README.md)), results `gear-train-check-20261114-140356` (SolidWorks 2026 34.1.1) and `gear-train-check-20261114-140631` (2024 SP5 32.5.0): on both versions the walk read
  `Folder A`, its mate, `Folder B`, its mate, `Folder2___EndTag___`,
  `Folder1___EndTag___`, the same after a reopen; `FeatureByName` found both
  mates; suppressing `Folder A` suppressed both and unsuppressing it brought
  them back.

## See also

- [assemblies/02 — Mates from code](02-mates-from-code.md) — making mates; the `MateGroup` walk to find one
- [assemblies/05 — Test motion with the drag operator](05-test-motion-with-the-drag-operator.md) — whether the mates you read let it move
- [reading/12 — Snapshot suppression before you suppress](../reading/12-snapshot-suppression-before-you-suppress.md)
- [curves/11 — Feature tree folders](../curves/11-feature-tree-folders.md) — folder markers and end tags in a part
- [connect/05 — Choosing among versions](../connect/05-choosing-among-versions.md) — attaching to 2024 or 2025
- [connect/10 — Driving from outside Windows](../connect/10-driving-from-outside-windows.md)
- [GOTCHAS §19, §74, §75, §76](../../GOTCHAS.md)
- [assemblies/07 — Configurations that hold different positions](07-configurations-that-hold-different-positions.md) — `IsSuppressed2` across configurations, and `EntityParams` as a position check
- [assemblies/10 — Mate a gear train that turns](10-mate-a-gear-train-that-turns.md) — making gear and lock mates; which way the ratio goes in and comes back
- [assemblies/13 — Assembly configurations from code](13-assembly-configurations-from-code.md) — the walk and `IsSuppressed2` with mates suppressed in some configurations
