---
id: documents-02-save-as-and-close
title: Save a document to a new path, and close it
status: verified
verified_on: SolidWorks 2026 (revision 34.0.0); closing assemblies also on 34.1.1 and SolidWorks 2024 SP5 (32.5.0)
language: [python]
api: [IModelDocExtension.SaveAs3, IModelDoc2.SaveAs3, IModelDoc2.GetPathName, IModelDoc2.GetTitle, IModelDoc2.GetSaveFlag, ISldWorks.CloseDoc, ISldWorks.QuitDoc]
keywords: [SaveAs3, save as, overwrite, silent overwrite, swSaveAsOptions_Silent, swSaveAsCurrentVersion, out parameter, tuple, CloseDoc, close without saving, GetSaveFlag, GetPathName, unsaved changes, QuitDoc, Save Modified Documents dialog, modal dialog hangs, SOLIDWORKS CAM Warning, close an assembly, 0x80010105, document will not close]
answers: "How do I save a new document to a path from code, and close a document without a prompt?"
---

# Save a document to a new path, and close it

## What this is for

A tool that builds a part has to put it somewhere, and a probe or a batch job
has to close what it made without a dialog waiting for someone. Both calls are
short. Both do something you might not want without saying so: `SaveAs3`
replaces an existing file, and `CloseDoc` throws away unsaved changes.

## The call

```python
SAVE_AS_SILENT = 1           # swSaveAsOptions_e.swSaveAsOptions_Silent


def save_as(self, path: str) -> str:
    """Save the build's document to a new path, and report where it went.

    Probe save_as: ``IModelDocExtension.SaveAs3`` returned a plain True and
    silently overwrote an existing file, so an existing path is refused here
    before SolidWorks is asked.
    """
    if os.path.exists(path):
        raise SolidWorksError(f"{path} already exists, and a build never overwrites a file.")
    doc = self._doc()
    saved = call(call(doc, "Extension"), "SaveAs3", path, 0, findings.SAVE_AS_SILENT, _null_dispatch(),
                 _null_dispatch(), _out_long(), _out_long())
    if not saved:
        raise SolidWorksError(f"SolidWorks would not save {call(doc, 'GetTitle')} as {path}.")
    kept = str(call(doc, "GetPathName"))
    if kept.lower() != path.lower():
        raise SolidWorksError(f"SolidWorks saved to {kept!r}, not {path!r}.")
    return kept

def close_document(self, title: str) -> None:
    """``CloseDoc`` closes without asking, modified or not (probe close_document)."""
    call(self._app, "CloseDoc", title)
```

`call`, `_null_dispatch()` and `_out_long()` are from
[connect/02](../connect/02-attach-from-python.md): the late-bound helper, an
absent COM object typed as `VARIANT(VT_DISPATCH, None)`, and a by-reference
integer `VARIANT(VT_BYREF | VT_I4, 0)`.

- `SaveAs3(path, version, options, exportData, advancedSaveAsOptions, out errors, out warnings)`
  on **IModelDocExtension**. `0` is the current version and `1` silent, from
  the probe's constants read out of `swconst.tlb`. The two nulls and two outs
  are the argument types that ran; what the out values held was not read.
- `GetPathName` and `GetTitle` on **IModelDoc2**. After the save the document
  *is* the new file: its title and path both change.
- `CloseDoc(title)` on **ISldWorks**, by the document's title.

The path was always a local drive path (`C:\...`). The tool refuses anything
else before it asks; see "What it does not do".

## Why it is not obvious

**It overwrites without a word.** Saving a second time onto the same path with
the same silent option returned `True`, and the file on disk changed size
(36249 to 35405 bytes). There is no prompt with the silent flag and no
distinct return. If overwriting would be wrong, check the path yourself first,
as `save_as` does.

**The flag came back plain, not as a tuple.** In pywin32, passing
by-reference arguments often makes a call return a tuple of the result and the
outs. `IModelDocExtension.SaveAs3` with two `_out_long()` outs returned a bare
`True` both times. Code that does `result[0]` would raise; code that tests
`bool(result)` is right either way. The probe hedged:

```python
def _flag(result: Any) -> Any:
    """SaveAs3 with by-reference outs comes back as a tuple whose first item is the flag."""
    return result[0] if isinstance(result, tuple) and result else result
```

and recorded `save_as3_result_is_tuple = False`.

**`IModelDoc2.SaveAs3` is a different call with a different answer.** On a
second new part, `call(doc, "SaveAs3", path, 0, 1)` returned `0`, and the file
was on disk. Do not read that `0` as `False`. This entry uses the extension's
form, whose `True` did mean saved.

**`CloseDoc` does not ask.** A part was made, a sketch with one point was
added (`GetSaveFlag` read `True`: modified), and it had never been saved.
`CloseDoc(title)` returned `None`, and the part was gone from the open
documents with no prompt. That is what a probe or a batch wants, and exactly
what an interactive tool must not do to a document the user was editing: close
only what your code made, by the title it had when you made it. That was a
part on SolidWorks 2026. **On SolidWorks 2024, `CloseDoc` on an assembly whose
saved parts had changed did ask**, in a modal dialog; see
[Closing an assembly](#closing-an-assembly-closedoc-quitdoc-and-the-dialogs-they-raised).

## Closing an assembly: CloseDoc, QuitDoc, and the dialogs they raised

Added from the Gear-Generator's probes and end-to-end checks, SolidWorks 2026
(34.0.0, 34.1.1) and 2024 SP5 (32.5.0), Python over pywin32 late binding. A
modal dialog blocks every COM call until someone answers it, so a script that
meets one hangs.

**`CloseDoc` on SolidWorks 2024 asked about modified parts.** Closing a probe's
scratch assembly whose saved component parts had been changed opened a modal
"Save Modified Documents" dialog on 2024, and the probe hung (no answer in
600 s); SolidWorks 2026 closed the same assembly without asking. The probe's
fix was to save its own modified parts before closing an assembly (condensed
from the probe: the same calls, its error handling and records removed; not run
as written; `created` is the set of titles the script itself made):

```python
import pythoncom
from win32com.client import VARIANT

SW_DOC_PART, SAVE_AS_CURRENT, SAVE_AS_SILENT = 1, 0, 1


def call(obj, name, *args):
    member = getattr(obj, name)
    return member(*args) if args else member


def null():
    return VARIANT(pythoncom.VT_DISPATCH, None)


def out_long():
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)


def save_created_parts(app, created):
    """Save, in place, every modified part this script made and had already saved to a path."""
    doc = call(app, "GetFirstDocument")
    while doc is not None:
        title = str(call(doc, "GetTitle"))
        path = str(call(doc, "GetPathName") or "")
        if title in created and path and int(call(doc, "GetType")) == SW_DOC_PART and call(doc, "GetSaveFlag"):
            call(call(doc, "Extension"), "SaveAs3", path, SAVE_AS_CURRENT, SAVE_AS_SILENT,
                 null(), null(), out_long(), out_long())
        doc = call(doc, "GetNext")
```

Every 2024 run after that fix closed its assemblies. That is only right for
files your own code made: saving is not an option for a user's documents.

**`QuitDoc` closed modified documents without a dialog.** `QuitDoc(title)` on
**ISldWorks** closes a document **without saving**, the way a person answering
"Don't save" would (condensed from the check that ran it; not run as written):

```python
import os

SW_DOC_ASSEMBLY = 2


def documents(app):
    out, doc = [], call(app, "GetFirstDocument")
    while doc is not None:
        out.append(doc)
        doc = call(doc, "GetNext")
    return out


def quit_in(app, folder):
    """Close every open document under folder WITHOUT saving (ISldWorks.QuitDoc), assemblies
    first; returns the titles still open under it."""
    root = os.path.normcase(os.path.abspath(folder)) + os.sep

    def under(path):
        return bool(path) and os.path.normcase(os.path.abspath(path)).startswith(root)

    for kind in (SW_DOC_ASSEMBLY, SW_DOC_PART):
        for doc in documents(app):
            if under(str(call(doc, "GetPathName") or "")) and int(call(doc, "GetType")) == kind:
                call(app, "QuitDoc", str(call(doc, "GetTitle")))
    return [str(call(d, "GetTitle")) for d in documents(app) if under(str(call(d, "GetPathName") or ""))]
```

On an assembly and the parts an update had just changed and not saved,
assembly first, it closed every one with nothing left open and **no dialog**
(the script runs a dialog watcher that logs any window SolidWorks opens; it
logged none there), on SolidWorks 2026 34.0.0 and 34.1.1 and on 2024 SP5. The
files on disk were not changed.

**Closing an assembly with unsaved changes while its changed parts are open in
their own windows asked nothing — by `CloseDoc` or by `QuitDoc`, on 2026 and
2024.** Two parts of a mated assembly were changed in their own documents
(opened by path and activated) and the assembly updated, nothing saved: the
assembly and both parts read `GetSaveFlag` `True`. `CloseDoc` on the assembly
returned at once (0.3 s), and the probe's dialog watch saw **no window** open.
The two parts stayed open, still modified; `CloseDoc` on each closed it
silently. Afterwards no file on disk had been written (modification times
unchanged) and the parts reopened with their saved values. `QuitDoc`, in the
same order on a second copy, did exactly the same.

That differs from the 2024 "Save Modified Documents" case above, which was
**observed once** and not reproduced since. In that probe the parts were also
still open in their own windows (it closed them after the assembly), so being
open is not the difference. What differed is how the parts came to be modified:
there through the assembly (a mate linked to a global, and `ForceRebuild3(False)`,
which marks every component, [assemblies/12](../assemblies/12-rebuild-scope-and-the-save-flag.md)),
here by edits made in each part's own document before the assembly was
updated. Which difference decides whether 2024 asks is **not known**.

**But on 2026, `QuitDoc` on an assembly saved by SolidWorks 2024 raised a modal
"SOLIDWORKS CAM Warning: Save changes to <assembly>?"**, from the SOLIDWORKS CAM
add-in, once for each of two such assemblies. Every document of those
assemblies had read `GetSaveFlag` `False` straight after the open, and nothing
was done to them in between except reading `GetSaveFlag` and trying
`IModelDocExtension.GetVersionHistory` (which raised `<unknown>.GetVersionHistory`
through late binding). The flag was **not read again just before the close**,
so what it read when the prompt came up is not known. The run was unblocked from
outside: a separate Python process found the dialog's "&No" button
(`win32gui.EnumChildWindows`) and posted it `BM_CLICK`; nothing was saved and
every file's sha256 and mtime compared equal afterwards. A 2026-made assembly
closed by `QuitDoc` raised no such prompt. Whether the add-in asks with the add-in
unloaded, or for a 2024 file that was saved again in 2026, was not tried.

**After `ModifyDefinition` on a gear mate, SolidWorks 2024 could not close the
assembly at all**: `CloseDoc` raised `0x80010105` and later closes left it open
without a word ([assemblies/11](../assemblies/11-change-a-mated-gear-train.md#the-ratio-change-that-strands-an-assembly-on-2024)).

## What it does not do

- **Network and WSL paths are untested.** Every save here went to a local drive
  path under `C:\Users\...\Documents`. Whether `SaveAs3` accepts a
  `\\wsl.localhost\...` UNC path is an open question; settling it takes one
  save to such a path and a check that the file arrived.
- The error and warning out values were never read, so no failure codes are
  recorded here.
- Saving in an older version, or exporting another format, was not tried.
- Only a part was saved through `save_as` itself; the assembly probe saved its
  two parts with the same `IModelDocExtension.SaveAs3` call before inserting
  them.

## Evidence

SolidWorks 2026 (revision 34.0.0), Python over pywin32, probe run
20260914-180426. Probes `save_as` and `close_document`, in
[`code/python/gear_generator/probe/`](../../code/python/gear_generator/probe/p3_files.py).

- `SaveAs3(path, current version, silent, null, null, out long, out long)`:
  returned `True`; `save_as3_result_is_tuple = False`; the file was on disk;
  `GetTitle` then read `Probe Save.SLDPRT` and `GetPathName` the new path.
- Onto the same path again: `{'flag': True, 'size_before': 36249, 'size_after': 35405}`.
- `IModelDoc2.SaveAs3` on another new part: `{'returned': 0, 'on_disk': True}`.
- `close_document`: `GetSaveFlag` `True`, `CloseDoc` returned `None`, and the
  title was no longer among the open documents.
- The probe run as a whole compared the open documents before and after all 33
  probes, and every scratch document had been closed this way without leaving
  one behind or closing one that was open before.
- The tool's own build saved its finished gear through `save_as` above.
- Closing assemblies: the 2024 hang is run 20261102-211723 on SolidWorks 2024
  SP5 (`assembly_distance_link` "HUNG … no answer in 600 s; a dialog may be open
  in SolidWorks", 7 probes not run after it; the dialog's title is named in the
  notes kept beside the results); the fixed probe passed every
  assembly probe in run 20261103-130406 (44 of 44). `QuitDoc`: the
  Gear-Generator's end-to-end check, section "a3", on SolidWorks 2026 34.0.0
  (2026-11-13), 34.1.1 and 2024 SP5 (both 2026-11-14), each "this section's
  documents closed in SolidWorks without saving: left []", with no dialog
  logged in the section. The CAM warning: two runs of its cross-version open
  check on SolidWorks 2026 34.1.1, 2026-11-14, each logging
  "every document … reads GetSaveFlag False straight after the open: marked []"
  and "closed without saving (QuitDoc): left []"; the dialog itself is not in
  those logs (the check has no dialog watcher) and is recorded in the check's
  own notes. The unsaved close with the parts open: probe
  `unsaved_update_close`, SolidWorks 2026 34.1.1 (run 20261114-095421) and 2024
  SP5 32.5.0 (run 20261114-102300), each in a session started fresh:
  `unsaved_update_close_asks = {'CloseDoc': False, 'QuitDoc': False}`,
  `unsaved_update_close_discards = {'CloseDoc': True, 'QuitDoc': True}`, the
  assembly's close `{'dialog': False, 'windows': [], 'seconds': 0.3}` (0.36 on
  2024), `written: []`. Those logs and results are kept in the Gear-Generator
  repository, not here.

## See also

- [documents/01 — New part from a template](01-new-part-from-template.md)
- [connect/07 — Find the open document](../connect/07-find-the-open-document.md) — the title `CloseDoc` wants
- [connect/10 — Driving from outside Windows](../connect/10-driving-from-outside-windows.md) — where files should live when the code is in WSL
- [assemblies/01 — New assembly and insert components](../assemblies/01-new-assembly-and-insert-components.md) — parts must be saved before they can be inserted
- [GOTCHAS §34](../../GOTCHAS.md)
- [files/01 — Batch-convert STEP](../files/01-batch-convert-step.md) — `CloseDoc` in a batch, and `IModelDocExtension.SaveAs` with error codes
- [files/04 — Export a body to STEP](../files/04-export-a-body-to-step.md) — `IModelDocExtension.SaveAs` with the copy option, so the document keeps its name
- [assemblies/12 — Rebuild an assembly without marking every part modified](../assemblies/12-rebuild-scope-and-the-save-flag.md) — what sets `GetSaveFlag`, so there is less to close
- [assemblies/11 — Change a mated gear train](../assemblies/11-change-a-mated-gear-train.md) — the assembly 2024 could not close
- [GOTCHAS §97, §100](../../GOTCHAS.md)
