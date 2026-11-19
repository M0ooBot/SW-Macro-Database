---
id: G21
title: A late-bound host cannot call an API with a `ByRef Long` out-parameter
always: false
members: [OpenDoc6, LoadFile4]
languages: [pywin32, late-bound]
---

`OpenDoc6` and `LoadFile4` both take one. VBScript and PowerShell are
late-bound, cannot produce `VT_BYREF|VT_I4`, and fail with **"Type mismatch"
before the method runs** — so the failure looks like a bad argument list rather
than a host limitation, and no amount of rearranging the call fixes it.

VBA inside SolidWorks works, because it is in-process. C# compiled against the
interop assemblies works, because it is early-bound. Python gets there with an
explicit typed variant, `VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)`, as
in §4.

This is the reason a job may have to be a compiled exe rather than the `.vbs`
that everything else in this repo uses.
