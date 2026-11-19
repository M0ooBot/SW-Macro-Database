---
id: G0
title: What goes wrong, as a statement someone would recognise
always: false
members: [IInterface.Member, BareMember]
languages: [all]
---

Copy this file to `gotchas/NNN-short-slug.md` with the next free number, and set
`id` to `G` and that number. Numbers never change: `GOTCHAS §N` is cited
throughout. Do not write the `## N.` heading: `GOTCHAS.md` is generated from the
title, by `python3 tools/build_manifest.py`.

Then say what was called, on what, and what happened instead, with the version
(`SolidWorks 2026 (34.1.1)`). Then what to do instead, and how to notice. Link
the entry that has the details, written from this folder:
[entries/…](../entries/…). Another gotcha is a sibling file:
[§55](055-a-zero-argument-member-that-returns-nothing-or.md).

- `members`: the API members the gotcha is about, `Interface.Member` where you
  know the interface, else the bare member. Not every member it mentions: leave
  out the check you recommend and the fix, unless the trap is in them too.
- `languages`: `all`, or the bindings it bites: `csharp`, `pywin32`,
  `late-bound` (VBScript, PowerShell, pywin32's dynamic dispatch).
- `always`: `true` only for the short always-list (silent, destructive or most
  common failure modes), which the skills show in full. Ask the owner first.
