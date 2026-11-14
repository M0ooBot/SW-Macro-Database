---
id: assemblies-12-rebuild-scope-and-the-save-flag
title: Rebuild an assembly without marking every part modified, and what sets GetSaveFlag
status: verified
verified_on: SolidWorks 2026 (revision 34.1.1) and SolidWorks 2024 SP5 (32.5.0); the mated-train half on 2024 ran beside a stranded assembly, as noted
language: [python]
api: [IModelDoc2.ForceRebuild3, IModelDoc2.EditRebuild3, IModelDoc2.GetSaveFlag, IModelDocExtension.NeedsRebuild, IModelDocExtension.NeedsRebuild2, ISldWorks.OpenDoc6, ISldWorks.ActivateDoc3, IModelDocExtension.GetWhatsWrongCount, IComponent2.Transform2]
keywords: [ForceRebuild3 True, ForceRebuild3 False, top only, EditRebuild3, rebuild marks parts modified, save prompt for parts not changed, GetSaveFlag, unsaved changes, dirty flag, modified flag, NeedsRebuild, NeedsRebuild2, rebuild returns False, failed component, interference check marks modified, OpenDoc6 warning 128, swFileLoadWarning_AlreadyOpen, ActivateDoc3, skeleton part, layout part, opened from file reads unmodified]
answers: "Which rebuild should I call on an assembly after changing it from code, so that SolidWorks only asks to save the documents I actually changed — and what marks a document modified in the first place?"
---

# Rebuild an assembly without marking every part modified

## What this is for

A tool that changes an assembly (moves a component, changes a skeleton part's
globals, changes one part) and rebuilds it leaves documents marked modified.
SolidWorks then asks to save each of them when the user closes, and saving
rewrites files that may be shared with other assemblies. With the wrong rebuild
call, **every** component is marked, including parts nothing touched. This entry
is which rebuild marks what, what each returns when a component fails, what
`GetSaveFlag` reads straight after an open, and which other calls set it.

## The calls

From the Gear-Generator probe (`assembly_rebuild_scope` in its tier 7,
`mated_rebuild_scope` in `p8_motion.py`), Python over pywin32 late binding.

**The routes compared**, each on its own copy of an assembly:

```python
def _apply_route(px: Px, asm: Any, route: str, label: str) -> Dict[str, Any]:
    """Rebuild the assembly by one route; what it returned (``None`` for no rebuild at all)."""
    if route == "none":
        return {"returned": None}
    thunks = {"ForceRebuild3(True)": lambda: call(asm, "ForceRebuild3", True),
              "EditRebuild3": lambda: call(asm, "EditRebuild3"),
              "ForceRebuild3(False)": lambda: call(asm, "ForceRebuild3", False)}
    got, value = px.attempt(f"{route} on the assembly, {label}", thunks[route])
    return {"returned": plain(value) if got else "raised"}
```

`ForceRebuild3(topOnly)` and `EditRebuild3` on **IModelDoc2** (the assembly).

**Every document's flag, by path**, after each step:

```python
def _doc_at(px: Px, path: str) -> Any:
    doc = call(sc.app(px), "GetFirstDocument")
    guard = 0
    while doc is not None and guard < 500:
        guard += 1
        if same_path(str(call(doc, "GetPathName") or ""), path):
            return doc
        doc = call(doc, "GetNext")
    return None


def _save_flags(px: Px, paths: Mapping[str, str]) -> Dict[str, Optional[bool]]:
    """``GetSaveFlag`` of each labelled document; None for one not in memory."""
    out: Dict[str, Optional[bool]] = {}
    for label, path in paths.items():
        doc = _doc_at(px, path)
        out[label] = None if doc is None else bool(call(doc, "GetSaveFlag"))
    return out
```

`GetFirstDocument` on **ISldWorks**, `GetNext`, `GetPathName` and `GetSaveFlag`
on **IModelDoc2**. Component parts loaded only by their assembly are in that
list too.

**Whether SolidWorks says a rebuild is needed**: the probe listed every member
of `IModelDoc2` and `IModelDocExtension` in the installed `sldworks.tlb` whose
name says so and takes no argument — that was `IModelDocExtension.NeedsRebuild`
and `NeedsRebuild2` on both versions — and read them, never calling anything
that rebuilds:

```python
def _rebuild_status(px: Px, doc: Any, members: Mapping[str, Sequence[str]], label: str) -> Dict[str, Any]:
    """One read of each listed rebuild-status member; what each answered."""
    out: Dict[str, Any] = {}
    for interface, names in members.items():
        owner = doc if interface == "IModelDoc2" else sc.extension(doc)
        for name in names:
            got, value = px.attempt(f"{interface}.{name} ({label})", lambda n=name, o=owner: member(o, n)[0])
            out[f"{interface}.{name}"] = plain(value) if got else "raised"
    return out
```

(`member` reads a zero-argument member and calls it only if a method came
back, [assemblies/03](03-interference-detection.md).)

## What each rebuild marked

**Assembly of fixed components.** Two gear parts and a body-less skeleton part
(planes and shaft axes driven by globals), each placed by frame and fixed,
built, saved, closed and opened again. Then, in order and without saving: a
`Transform2` put turning the second gear half a tooth and back; the skeleton's
shaft position changed by 5 mm in its own document (opened by path, rebuilt
there); the second gear's tooth-count global changed in its own document; and a
global set so that the second gear's hole cut failed. After each, the route ran
on the assembly. Documents read `GetSaveFlag` True afterwards (cumulative):

| Route | after the put | after the skeleton change | after the part change |
|---|---|---|---|
| `ForceRebuild3(True)` | assembly | assembly, skeleton | assembly, skeleton, changed gear |
| `EditRebuild3` | assembly | assembly, skeleton | assembly, skeleton, changed gear |
| `ForceRebuild3(False)` | **assembly, skeleton, both gears** | same | same |
| no rebuild | nothing | assembly, skeleton | assembly, skeleton, changed gear |

- **`ForceRebuild3(False)` marked the gear nothing had changed**, and every
  other document, at the first step. That is what makes SolidWorks ask to save
  every part.
- **`ForceRebuild3(True)` and `EditRebuild3` marked exactly the documents
  changed on purpose**, never the untouched gear, before and after the
  interference check.
- **Every route, and no rebuild at all, showed the change**: the put's frame
  read back, the half-tooth put clashed with the other gear and was clean put
  back, the moved shaft axis measured 5 mm further in the assembly
  ([reading/16](../reading/16-measure-between-two-selections.md)), and the gear
  with a new tooth count clashed at its old frame. So the rebuild here is for
  the mark and the report, not for the picture.
- **With a component failing**, all three routes returned **`False`** (and
  `True` once the part was put right); with no rebuild nothing reported the
  failure. The failed cut read `GetErrorCode2` 1 on 2026 and 51 on 2024, and
  `IModelDocExtension.GetWhatsWrongCount` read 1. Tried first, the gear's
  face-width global set to 0 failed nothing: the part's rebuild returned
  `True` and no feature reported an error, so it could not serve as the
  failing case.

**Mated gear train.** A train mated as in
[assemblies/10](10-mate-a-gear-train-that-turns.md) (gear axes coincident with
skeleton axes, an axial distance mate on an assembly global, a compound pair
locked, gear mates, an angle-mate drive on an assembly global), saved,
reopened, one copy per route. Steps: the axial global +4 mm; the drive +30°; the
compound anchor put 7° round under its suppressed lock; the output shaft moved
5 mm in the skeleton's document; the gear part's outside diameter +4 mm in its
own document; an angle mate added against the compound lock, then deleted.

- `ForceRebuild3(True)` and `EditRebuild3` **re-solved every change** (the axial
  move and the drive read 0 before the route and the whole change after it) and
  marked only what had changed: the assembly for the axial global, the drive and
  the put; then the skeleton; then the part. `ForceRebuild3(False)` re-solved
  them too but marked the skeleton and the part at the first step.
- With the conflicting mate, **no route returned `False`**: `AddMate5`'s status
  was 5 and the mate errors showed before and after the route; deleted, they
  cleared ([assemblies/02](02-mates-from-code.md#when-a-mate-is-refused-or-over-defines)).

## What sets GetSaveFlag

- **A document just opened from its file reads `False`** — every document of a
  reopened assembly, parts loaded only as its components included, on both
  versions; also every document of an assembly saved by SolidWorks 2024 and
  opened in 2026 (nothing was converted on disk: every file's sha256 and mtime
  compared equal afterwards).
- **A `Transform2` put alone did not mark the assembly.** It was marked by what
  came after.
- **An interference check marks the assembly; reading component frames does
  not.** After a reopen, reading every component's `Transform2` left every flag
  `False`; running the interference check
  ([assemblies/03](03-interference-detection.md)), with nothing found, marked
  the assembly. Six reopens on each version.
- A rebuild marks as in the tables above; a change made in a part's or the
  skeleton's own document marks that document.

## NeedsRebuild, and a change made in another window

- `NeedsRebuild` read `True` and `NeedsRebuild2` 1 after an **assembly** global
  changed (the axial global, the drive), and `False` / 0 after every route, the
  top-only one included, on both versions.
- After a change made in the skeleton's or the part's **own document**, read
  on the assembly before any rebuild: `False` / 0 on 2026, `True` / 1 on 2024.
- On 2026 the moved shaft **already showed in the assembly once `ActivateDoc3`
  brought the assembly back to the front**, before any rebuild (0 mm before the
  activate, 5 mm after); on 2024 it showed only after the route.

Those last two differences are **open**: the 2024 run they come from shared its
session with an assembly that could not be closed and that held the same
skeleton and part open ([assemblies/11](11-change-a-mated-gear-train.md#the-ratio-change-that-strands-an-assembly-on-2024)),
so they may be that assembly's doing rather than the version's. A clean rerun
on 2024 is in flight.

## Changing a component in its own document

The changes above were made by opening the part by its path and making it
active, the way a tool edits a part that is already loaded as a component:

- `ISldWorks.OpenDoc6(path, type, 1, "", out errors, out warnings)` (option 1
  is `swOpenDocOptions_Silent`, read from `swconst.tlb`) returned the document
  itself, not a tuple, and made a closed part active. On a part **already
  open**, including one loaded only as a component of an open assembly, it
  returned the same document with warning **128**
  (`swFileLoadWarning_AlreadyOpen`) and did **not** bring it to the front.
  Follow it with `ActivateDoc3(title, False, 0, out)`
  ([connect/07](../connect/07-find-the-open-document.md)), which did. Both
  versions.

## Why it is not obvious

- `ForceRebuild3(False)` is the call most code uses, and it looks harmless
  because the geometry is right either way. The cost only shows when the user
  closes and is asked to save parts nothing touched.
- `topOnly = True` reads like "skip the components", but it still re-solved
  mates driven by assembly globals and picked up changes made in the
  components' own documents.
- A rebuild's `True` says nothing about over-defined mates: check `AddMate5`'s
  status and every mate's `GetErrorCode2` instead.

## What it does not do

- Measured on assemblies of fixed components and on mated gear trains only. A
  gear-pair assembly with a centre-distance equation, point mates and angle
  mates between non-parallel axes
  ([assemblies/04](04-mates-between-non-parallel-axes.md)) was not measured.
- **Not yet shown:** a train *built* under the top-only rebuild (the probe's
  trains were built with the full one), a drive after a shaft move under it,
  and a put plus top-only rebuild while `CommandInProgress` is set
  ([curves/08](../curves/08-rebuild-once-at-the-end.md)). A probe round adding
  the first two is in flight.
- The failed-rebuild case was a failing part only; a failing mate was the
  conflicting-mate case, where every route returned `True`.
- Whether a static assembly still reports needing a rebuild after the top-only
  route was not read there; only the mated train's `NeedsRebuild` was.

## Evidence

- Static assembly: SolidWorks 2026 34.1.1, full runs 20261114-013909 (76 of 76)
  and 20261114-034458 (83 of 83); SolidWorks 2024 SP5 32.5.0, run
  20261114-014813 (27 of 27) in a SolidWorks started for the run.
  `flags_on_open` all `False` for every route; `rebuild_marked` as in the table;
  `rebuild_verdicts`: `only_changed_marked` true for `ForceRebuild3(True)` and
  `EditRebuild3`, false for `ForceRebuild3(False)` and none;
  `failure_reported` true for the three routes, false for none;
  `ForceRebuild3(True) on the assembly, a failed part` returned `False`. With no
  rebuild, the put read `flags` all `False` and `flags_after_reads` the
  assembly `True`.
- Mated train: SolidWorks 2026 34.1.1, run 20261114-034458; SolidWorks 2024
  32.5.0, run 20261114-040636 (beside the stranded assembly).
  `mated_rebuild_keeps_components_unmodified = True`;
  `mated_rebuild_returned` all `True`; `rebuild_status_members = {'IModelDoc2': [], 'IModelDocExtension': ['NeedsRebuild', 'NeedsRebuild2']}`;
  for `ForceRebuild3(True)`, the axial step `status_before_route = {'NeedsRebuild': True, 'NeedsRebuild2': 1}`
  and `status = {False, 0}`; the skeleton step `before_activate_mm 0.0`,
  `before_route_mm 5.0` on 2026 and `0.0` on 2024.
- Opened-from-file flags and what marks the assembly: the Gear-Generator's
  own end-to-end check on 2026 34.1.1 and 2024 32.5.0, 2026-11-14 (322 of 322
  checks each): `marked modified after the frame reads (component_frame): []`
  and `marked modified after interferences() (0 found): ['<assembly>']` after
  each of six reopens. The 2024-saved assembly opened in 2026: every
  `GetSaveFlag` `False` straight after the open, six files unchanged.
- `OpenDoc6` / `ActivateDoc3`: probes `open_and_activate_part` and
  `open_part_from_assembly`, 2026 34.1.1 (20261114-034458) and 2024 32.5.0
  (20261113-184353): `open … warnings 128`, `open_doc_on_open_part = {'made_active': False, 'same_title': True}`.

The result files are kept in the Gear-Generator repository, not here.

## See also

- [curves/08 — Rebuild once at the end](../curves/08-rebuild-once-at-the-end.md) — `ForceRebuild3` versus `EditRebuild3` on a part, and its timing
- [documents/02 — Save as, and close](../documents/02-save-as-and-close.md) — `GetSaveFlag` and closing without a prompt
- [assemblies/03 — Interference detection](03-interference-detection.md) — the check that marks the assembly
- [assemblies/04 — Mates between non-parallel axes](04-mates-between-non-parallel-axes.md) — the `Transform2` put
- [assemblies/10 — Mate a gear train that turns](10-mate-a-gear-train-that-turns.md)
- [assemblies/11 — Change a mated gear train](11-change-a-mated-gear-train.md)
- [reading/16 — Measure between two selections](../reading/16-measure-between-two-selections.md)
- [connect/07 — Find the open document](../connect/07-find-the-open-document.md)
- [GOTCHAS §58, §93, §100](../../GOTCHAS.md)
