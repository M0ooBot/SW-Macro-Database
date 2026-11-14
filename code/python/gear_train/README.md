# Gear-train check

`gear_train_check.py` builds a small gear train from nothing in a SolidWorks it starts itself, then
runs, as written, the listings that these entries quote, and records what every call returned:

- [assemblies/10 — Mate a gear train that turns](../../../entries/assemblies/10-mate-a-gear-train-that-turns.md)
- [assemblies/11 — Change a mated gear train](../../../entries/assemblies/11-change-a-mated-gear-train.md)
- [assemblies/12 — Rebuild scope and the save flag](../../../entries/assemblies/12-rebuild-scope-and-the-save-flag.md)
- [reading/16 — Measure between two selections](../../../entries/reading/16-measure-between-two-selections.md)
- and the additions to [assemblies/01](../../../entries/assemblies/01-new-assembly-and-insert-components.md),
  [assemblies/02](../../../entries/assemblies/02-mates-from-code.md),
  [assemblies/05](../../../entries/assemblies/05-test-motion-with-the-drag-operator.md),
  [assemblies/06](../../../entries/assemblies/06-read-every-mate.md) and
  [documents/02](../../../entries/documents/02-save-as-and-close.md).

Those entries were first written from the Gear-Generator's probe runs. This script exists so that
the code they quote is code that ran, with nothing project-specific in it.

**Status: not yet run.** Until a result file sits in `results/`, the entries keep their
"condensed from the probe, not run as written" marks.

## What it does

The fixtures are four plain cylinders, `GearA` to `GearD` (r 20 x 10 mm, each with a reference axis
`Gear Axis` made from its Top then Right planes), and a body-less skeleton part `Layout` with three
shaft axes `S1 Axis` to `S3 Axis` on +Z. A gear mate needs no teeth. The assembly `Train` holds
`GearA` on `S1`, `GearB` and `GearC` on `S2` (`GearC` locked to `GearB`, not mated to the shaft) and
`GearD` on `S3`, with gear mates `GearA : GearB` at 20 : 40 and `GearC : GearD` at 20 : 50
(illustrative numbers). Then, step by step:

1. the shaft mates (a concentric mate between two axes tried first, expected refused; the axes
   also selected through `GetCorresponding`), the lock, the gear mates, each mate renamed straight
   after its `AddMate5`; the mate statuses, error codes, `GetConstrainedStatus`, the ratio read back
   and `MateEntity(0)`;
2. a drive: an angle mate linked to a global, the global changed, every gear's turn measured;
3. `CreateMeasure` from a skeleton axis to the assembly's Right plane;
4. saved, closed, reopened: every `GetSaveFlag`, every component's `GetSuppression2`, both gear
   mates' definitions read, the flags again, the `MateGroup` walk;
5. `SetSuppression2` (unsuppress) on a lock already on, with the save flags straight around it;
6. a put re-phasing a gear with its gear mate on, then a drive; a put on a locked gear with its
   lock on, then a drive;
7. an over-defining angle mate: its `AddMate5` status, the error codes, `GetWhatsWrong`,
   `GetConstrainedStatus`, its code while suppressed, then deleted;
8. the lock suppressed and unsuppressed; the gear mate deleted and made again at a new ratio under
   its old name, its place in the `MateGroup`, the ratio read back, a drive;
9. assemblies/05's drag recipe on one gear, the drive suppressed;
10. mate folders: one, one nested inside it, the outer suppressed and unsuppressed; saved, closed,
    reopened and walked again;
11. for each of `ForceRebuild3(True)`, `EditRebuild3` and `ForceRebuild3(False)`, on its own copy:
    the save flags and `NeedsRebuild` around the route after a global change, and after a change made
    in the skeleton's own document;
12. an assembly with unsaved changes closed by `CloseDoc`, and on another copy by `QuitDoc`, while
    the changed part is open in its own window: the time, any dialog, what stayed open, and whether
    any file was written;
13. `AddComponent5` of a closed part, then a second new assembly beside an unsaved one.

**Left out on purpose**, and kept as prose with their probe evidence in the entries: interference
and its half-pitch control (they need real teeth); `ModifyDefinition` on a gear mate (it left
SolidWorks 2024 with an assembly it could not close); forcing lightweight components (the
SOLIDWORKS CAM add-in's modal box blocks the open); the cross-version open; the first-assembly drag
cases of assemblies/05.

## Safety

- It starts its own SolidWorks from the path given, and **refuses** if any SolidWorks is already
  registered in the Running Object Table, or if the one it started has a document open.
- It writes only under the scratch folder you give (which must be empty or new), and its two result
  files under `--out`.
- It closes what it opened and calls `ISldWorks.ExitApp` at the end; if SolidWorks has not gone
  60 s later, it kills that process (the one it started, by the PID its moniker named).
- A dialog watch logs every dialog box SolidWorks puts up and never answers one. A watchdog kills
  the SolidWorks it started if one step runs past `--step-timeout` seconds (600 by default) and
  writes what it has.
- The result files carry no scratch path (written as `<scratch>`), no home folder and no user name.

## Running it

Windows Python 3 with pywin32, on the machine with SolidWorks, nothing else of SolidWorks running:

```
python code\python\gear_train\gear_train_check.py --sldworks "C:\path\to\SLDWORKS.exe" --scratch C:\path\to\empty\scratch
```

From WSL, call the Windows Python (`python.exe`) with Windows paths for both arguments; the result
files land in `code/python/gear_train/results/` unless `--out` says otherwise. Run it once per
SolidWorks version, each with a new scratch folder. It took no measurement yet of its own length;
expect about a quarter of an hour per version.

Results: `results/gear-train-check-<stamp>.json` and `.txt`, one record per step with what each
call returned, the dialogs seen, and a summary. Exit code 0 when every step passed.
