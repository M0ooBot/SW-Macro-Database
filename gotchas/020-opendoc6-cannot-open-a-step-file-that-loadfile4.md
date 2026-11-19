---
id: G20
title: `OpenDoc6` cannot open a STEP file that `LoadFile4` opens fine
always: false
members: [ISldWorks.OpenDoc6, ISldWorks.LoadFile4, OpenDoc7, GetOpenDocSpec]
languages: [all]
---

On a vendor's STEP library, `ISldWorks.OpenDoc6` failed every file with error
**2097152, `swFileRequiresRepairError`**. It kept failing with import
diagnostics off, full entity check off, and several combinations of open
options. `ISldWorks.LoadFile4(path, "r", Nothing, err)` imported the same files
with `err = 0`.

`OpenDoc7` is not a way out: it rejects neutral formats before it starts.
`GetOpenDocSpec` on a `.step` returns `DocumentType = -1` and `Error = 1024`,
`swInvalidFileTypeError`. Renaming to `.stp` changes nothing.

The error number reads like the file is damaged. The files were fine.

This is about neutral formats. On native parts and assemblies `OpenDoc6` works
normally and is the call to use. See
[files/01](../entries/files/01-batch-convert-step.md).
