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
passes the result of `Parameterization2` with a `Tolerance` of 0.01 (metres).

What happened without it, on SolidWorks 2026 (34.1.1), from Python over pywin32:
`GetBSurfParams3(False, False, VARIANT(VT_DISPATCH, None), 1e-10, sense)` on a
lofted B-spline face ran for 19.2 s and then failed with `0x800706BE`, "The
remote procedure call failed": SolidWorks had ended. **One observation, with
confounds**: `Tolerance` was also 1e-10 rather than 0.01, the machine was short of
memory at that moment (another SolidWorks session and parallel builds were
running, about 2.3 GB of commit free), and an access violation in
`slduiu.dll` was logged. So Nothing is not proven to be the cause on its own. The
documented requirement is the fact; the crash is why it is worth obeying.

With `VP0 = surface.Parameterization2` (a zero-argument member, reached by
attribute access) and `Tolerance` 0.01, the same call on the same face returned
an `IBSurfParamData` in about 0.01 s in each of the three later runs, and the surface it
described was exact. Never pass Nothing; if `Parameterization2` returns nothing,
stop rather than call `GetBSurfParams3`. Code and evidence:
[entries/reading/17](../entries/reading/17-read-exact-b-spline-geometry.md).
