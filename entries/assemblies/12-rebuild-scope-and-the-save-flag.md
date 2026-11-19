---
schema: 2
id: assemblies-12-rebuild-scope-and-the-save-flag
title: Rebuild an assembly without marking every part modified, and what sets GetSaveFlag
answers: "Which rebuild should I call on an assembly after changing it from code, so that SolidWorks only asks to save the documents I actually changed — and what marks a document modified in the first place?"
keywords: [ForceRebuild3 True, ForceRebuild3 False, top only, EditRebuild3, rebuild marks parts modified, save prompt for parts not changed, GetSaveFlag, unsaved changes, dirty flag, modified flag, NeedsRebuild, NeedsRebuild2, rebuild returns False, failed component, interference check marks modified, OpenDoc6 warning 128, swFileLoadWarning_AlreadyOpen, ActivateDoc3, skeleton part, layout part, opened from file reads unmodified, CommandInProgress mates, origin noise, reading feature data marks nothing, unsuppress marks modified]
api: [IModelDoc2.ForceRebuild3, IModelDoc2.EditRebuild3, IModelDoc2.GetSaveFlag, ISldWorks.CommandInProgress, IFeature.GetDefinition, IModelDocExtension.NeedsRebuild, IModelDocExtension.NeedsRebuild2, ISldWorks.OpenDoc6, ISldWorks.ActivateDoc3, IModelDocExtension.GetWhatsWrongCount, IComponent2.Transform2]
language: [python]
status: verified
verified_on: SolidWorks 2026 (revision 34.1.1) and SolidWorks 2024 SP5 (32.5.0), each in a session started fresh for the run
majors: [32, 34]
evidence: []
recipe_status: null
recipe_evidence: []
superseded_by: null
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
`mated_rebuild_scope` in `p8_motion.py`), Python over pywin32 late binding. The
listings are copied from [`code/python/gear_train/gear_train_check.py`](../../code/python/gear_train/gear_train_check.py), which repeats them on its own fixtures.
It ran on SolidWorks 2026 (34.1.1) and 2024 SP5 (32.5.0), each started fresh by the runner (results `gear-train-check-20261114-140356` and `gear-train-check-20261114-140631` beside it).

**The routes compared**, each on its own copy of an assembly:

```python
def call(obj, name, *args):
    """Late-bound member: invoked when given arguments, read by attribute access otherwise."""
    member = getattr(obj, name)
    return member(*args) if args else member


def rebuild(asm, route):
    """One assembly rebuild by the route named; what it returned (None for no rebuild at all)."""
    if route == "ForceRebuild3(True)":
        return call(asm, "ForceRebuild3", True)       # top level only
    if route == "EditRebuild3":
        return call(asm, "EditRebuild3")
    if route == "ForceRebuild3(False)":
        return call(asm, "ForceRebuild3", False)      # everything
    return None
```

`ForceRebuild3(topOnly)` and `EditRebuild3` on **IModelDoc2** (the assembly).

**Every document's flag, by path**, after each step:

```python
import os


def doc_at(app, path):
    """The open document with this path, components loaded by an assembly included; None if not loaded."""
    want = os.path.normcase(os.path.abspath(path))
    doc = call(app, "GetFirstDocument")
    while doc is not None:
        have = str(call(doc, "GetPathName") or "")
        if have and os.path.normcase(os.path.abspath(have)) == want:
            return doc
        doc = call(doc, "GetNext")
    return None


def save_flags(app, paths):
    """GetSaveFlag of each labelled document; None for one not in memory."""
    out = {}
    for label, path in paths.items():
        doc = doc_at(app, path)
        out[label] = None if doc is None else bool(call(doc, "GetSaveFlag"))
    return out
```

`GetFirstDocument` on **ISldWorks**, `GetNext`, `GetPathName` and `GetSaveFlag`
on **IModelDoc2**. Component parts loaded only by their assembly are in that
list too.

**Whether SolidWorks says a rebuild is needed**: the probe listed every member
of `IModelDoc2` and `IModelDocExtension` in the installed `sldworks.tlb` whose
name says so and takes no argument (read with `pythoncom.LoadTypeLib`) — that
was `IModelDocExtension.NeedsRebuild` and `NeedsRebuild2` on both versions — and
read them, never calling anything that rebuilds:

```python
def read_member(obj, name):
    """A zero-argument member: read, and called only if late binding handed back a method."""
    value = call(obj, name)
    return value() if type(value).__name__ in ("method", "function") else value


def rebuild_status(doc):
    ext = call(doc, "Extension")
    return {"NeedsRebuild": read_member(ext, "NeedsRebuild"), "NeedsRebuild2": read_member(ext, "NeedsRebuild2")}
```

(`read_member` is the probe's way of reading a zero-argument member, as in
[assemblies/03](03-interference-detection.md); both came back as values.)

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
- Driven 30° after the put, after the skeleton move and after the part change,
  under each route, both trains turned at their ratio, the put's lock angle was
  kept and the output stayed on its moved axis; every frame matched the full
  rebuild's train to about 1e-13 mm.

**Building the train with the top-only rebuild alone.** Each route then also
*built* its own train from its own skeleton and gear part, with that route as
its only assembly rebuild (components placed by `Transform2` puts, the route,
the mates, the axial distance on an assembly global, the drive). Every build
passed the same check (18 `AddMate5` statuses 1, no mate error, every gear
under-defined; one drive made every gear fully defined; both trains turned at
their ratio), and its frames matched the full rebuild's build exactly. **The
full rebuild's build left the skeleton and the gear part modified; the
top-only and `EditRebuild3` builds left them unmodified**, before and after the
assembly was saved.

**Mates added under `CommandInProgress`.** With `ISldWorks.CommandInProgress`
set `True` (it read back `True`, and `False` after being set back), every unfix
and all 18 `AddMate5` calls of the train answered status 1, every mate code 0,
no gear moved, one top-only rebuild still under it; then one drive defined the
train and it turned at its ratio. A conflicting angle mate added under it
answered status 5 with the usual error codes. So the flag that speeds up a
batch of features ([curves/08](../curves/08-rebuild-once-at-the-end.md)) does not
get in the way of mating.

**Origin noise.** Every gear's origin, read at full precision before and after
`ForceRebuild3(True)`, moved **0.0 mm** after nothing, after a part's teeth
changed through its globals, and after another shaft moved 1 mm through the
skeleton's global (that shaft's own gear had already moved its full 1 mm by the
first read, once the assembly was active again). After a drive was added,
driven, set back and deleted, the largest move from before it was 2.8e-14 mm.
A "has it moved" tolerance of 1e-6 mm sits far above that.

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
- **Reading a gear mate's definition marks nothing.** On a reopened train
  (every flag `False`), `IFeature.GetDefinition` on each gear mate, then its
  `GearRatioNumerator` and `GearRatioDenominator`, then the object released (no
  `ModifyDefinition`, no `AccessSelections`): every flag stayed `False` after
  the get, after the reads and after the release, and the train then closed
  with nothing left open.
- **`SetSuppression2(1, 1, None)` (unsuppress) on a mate that was already on
  marks the assembly modified.** It returned `True`, left the lock on and raised
  no error. Every document's `GetSaveFlag` was read straight before the call and
  straight after it, with nothing in between: the assembly went from `False` to
  `True`, the skeleton and the part stayed `False`. So the mark is the call's
  own. Check `IsSuppressed2` before unsuppressing if the flag matters.

## NeedsRebuild, and a change made in another window

- `NeedsRebuild` read `True` and `NeedsRebuild2` 1 after an **assembly** global
  changed (the axial global, the drive), and `False` / 0 after every route, the
  top-only one included, on both versions.
- After a change made in the skeleton's or the part's **own document**, read
  on the assembly before any rebuild: `False` / 0, on both versions. So
  `NeedsRebuild` does not tell you that a component changed elsewhere.
- The moved shaft **already showed in the assembly once `ActivateDoc3`
  brought the assembly back to the front**, before any rebuild (0 mm before the
  activate, 5 mm after), on both versions.

A first 2024 run had read `True` / 1 there and not shown the move before the
route; it shared its session with an assembly SolidWorks could not close
([assemblies/11](11-change-a-mated-gear-train.md#the-ratio-change-that-strands-an-assembly-on-2024)),
which held the same skeleton and part open. In a fresh 2024 session neither
difference recurred, so they were that assembly's doing.

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
- **Not shown:** a component put plus a top-only rebuild while
  `CommandInProgress` is set; only mates were added under it.
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
- Mated train: SolidWorks 2026 34.1.1, full run 20261114-081921 (85 of 85);
  SolidWorks 2024 SP5 32.5.0, run 20261114-071324 (47 of 47), each in a session
  started fresh (an earlier pair, 20261114-034458 and the 2024 run
  20261114-040636 beside a stranded assembly, is superseded by these).
  `mated_build_rebuild_route = 'ForceRebuild3(True)'`;
  `mated_build_marked`: `ForceRebuild3(False)` `['layout', 'part']`, the other two
  `[]`; `mated_frames_against_reference` at most 1.2e-13 mm;
  `mated_rebuild_keeps_components_unmodified = True`;
  `mated_rebuild_returned` all `True`; `rebuild_status_members = {'IModelDoc2': [], 'IModelDocExtension': ['NeedsRebuild', 'NeedsRebuild2']}`;
  for `ForceRebuild3(True)`, the axial step `status_before_route = {'NeedsRebuild': True, 'NeedsRebuild2': 1}`
  and `status = {False, 0}`; the skeleton step `before_activate_mm 0.0`,
  `before_route_mm 5.0` and `status_before_route = {False, 0}` on both.
- `mates_under_command_in_progress`, `origin_noise`, `gear_mate_definition_read`:
  SolidWorks 2026 34.1.1, run 20261114-095421, and SolidWorks 2024 SP5, run
  20261114-102300 (49 of 49 each, fresh sessions).
  `mates_under_command_in_progress_hold = True`;
  `unsuppress_on_a_lock_already_on = {'returned': True, 'suppressed_after': False, 'marks_assembly': True, 'errors': {}}`,
  and, read straight around the call in runs 20261114-105135 (2026) and
  20261114-111150 (2024), `flags_before_call` all `False`, `flags_after_call`
  `{'assembly': True, 'layout': False, 'part': False}`, `marked_by_the_call = ['assembly']`;
  `origin_noise_mm = {'nothing': 0.0, 'part_global': 0.0, 'layout_move': 0.0, 'drive': 0.0, 'drive_start_to_end': 2.85e-14}`;
  `gear_mate_definition_read_marks = 'nothing'`.
- Opened-from-file flags and what marks the assembly: the Gear-Generator's
  own end-to-end check on 2026 34.1.1 and 2024 32.5.0, 2026-11-14 (322 of 322
  checks each): `marked modified after the frame reads (component_frame): []`
  and `marked modified after interferences() (0 found): ['<assembly>']` after
  each of six reopens. The 2024-saved assembly opened in 2026: every
  `GetSaveFlag` `False` straight after the open, six files unchanged.
- `OpenDoc6` / `ActivateDoc3`: probes `open_and_activate_part` and
  `open_part_from_assembly`, 2026 34.1.1 (20261114-034458) and 2024 32.5.0
  (20261113-184353): `open … warnings 128`, `open_doc_on_open_part = {'made_active': False, 'same_title': True}`.

- The listings, on a mated cylinder train: the gear-train runner ([`code/python/gear_train/`](../../code/python/gear_train/README.md)), results `gear-train-check-20261114-140356` (SolidWorks 2026 34.1.1) and `gear-train-check-20261114-140631` (2024 SP5 32.5.0), 25 of 25 steps each. Both versions: every flag
  `False` on open and after reading both gear mates' definitions; unsuppressing
  the lock that was on turned the assembly's flag alone `True`; after a global
  change, `NeedsRebuild` `True` / 1 before each route and `False` / 0 after; the
  top-only and `EditRebuild3` routes marked only the assembly, then the skeleton
  after its own change, and `ForceRebuild3(False)` every document; the moved
  shaft's gear already at its new place after `ActivateDoc3`, before the route.

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
- [GOTCHAS §58, §93, §100, §103](../../GOTCHAS.md)
