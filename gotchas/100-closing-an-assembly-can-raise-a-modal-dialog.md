---
id: G100
title: Closing an assembly can raise a modal dialog that hangs the script
always: true
members: [CloseDoc, QuitDoc]
languages: [all]
---

On SolidWorks 2024 SP5, `CloseDoc` on an assembly whose saved parts had been
changed through the assembly (its full rebuild marks every component, §93)
opened "Save Modified Documents" and the script hung; 2026 did not ask.
Observed once, not reproduced since.
`QuitDoc` (close without saving) closed modified documents with no dialog on
both. But on SolidWorks 2026 (34.1.1), `QuitDoc` on an assembly **saved by
2024** raised the SOLIDWORKS CAM add-in's "Save changes to <assembly>?",
although `GetSaveFlag` had read `False` after the open (it was not read again
before the close). A later probe, on 2026 with 2024-saved assemblies it had
changed, raised the same box from `CloseDoc`: a modal with Yes and No only,
which ignored `WM_CLOSE` and Escape; answered No, every file on disk was left
as it was. So it follows the file's older version and the add-in, not the
close call (an unsaved close of a same-version assembly asked nothing). An assembly with unsaved changes whose changed parts were
open in their own windows closed with no question by either call, on both
versions, and nothing was written. Why one case asked and the other did not is
not known: the cause is a reading of the two cases, not isolated (see
documents/02). See
[documents/02](../entries/documents/02-save-as-and-close.md#closing-an-assembly-closedoc-quitdoc-and-the-dialogs-they-raised).
