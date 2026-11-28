---
id: G118
title: `ISurface.GetBSurfParams3` needs its `VP0` from `ISurface.Parameterization2`; with Nothing, SolidWorks ended inside the call
always: false
members: [ISurface.GetBSurfParams3, ISurface.Parameterization2]
languages: [all]
---

`GetBSurfParams3(WantCubic, WantNonRational, VP0, Tolerance, out Sense)` types
`VP0` as a plain `IDispatch` in the type library, so Nothing goes through. The
SolidWorks API help, as quoted by its search index, says: "Before calling this
method, call ISurface:Parameterization2 to populate VP0", and its C# example
passes the result of `Parameterization2` with a `Tolerance` of 0.01 ("the allowed
deviation, in metres; default 0.01").

What happened without it, on SolidWorks 2026 (34.1.1), from Python over pywin32:
`GetBSurfParams3(False, False, VARIANT(VT_DISPATCH, None), 1e-10, sense)` on a
lofted B-spline face ran for 19.2 s and then failed with `0x800706BE`, "The
remote procedure call failed": SolidWorks had ended. **One observation, with
confounds**: `Tolerance` was also 1e-10 rather than 0.01; the part read was not
the saved file opened fresh but a copy already open in SolidWorks with unsaved
changes (opened read-only for viewing, its view changed); another SolidWorks
session and parallel builds were running, and the machine was reported short of
memory at the time; and an access violation in `slduiu.dll` was reported logged
then. None of these was examined further. So Nothing is not proven to be the cause on its own. The
documented requirement is the fact; the crash is why it is worth obeying.

With `VP0 = surface.Parameterization2` (a zero-argument member, reached by
attribute access) and `Tolerance` 0.01, the same call on the same face returned
an `IBSurfParamData` in about 0.01 s in each of the three later runs; in the
last, the surface it described was exact (the second stopped at
`GetControlPoints(0, 0)`, the third's check failed on the point layout). Never pass Nothing; if `Parameterization2` returns nothing,
stop rather than call `GetBSurfParams3`. Code and evidence:
[entries/reading/17](../entries/reading/17-read-exact-b-spline-geometry.md).
