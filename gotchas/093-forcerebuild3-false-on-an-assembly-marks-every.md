---
id: G93
title: `ForceRebuild3(False)` on an assembly marks every component modified
always: true
members: [ForceRebuild3]
languages: [all]
---

On an assembly, `ForceRebuild3(False)` marked every component document modified
(`GetSaveFlag` `True`), including parts nothing had changed, so closing asked
to save them all. `ForceRebuild3(True)` and `EditRebuild3` marked only the
documents changed on purpose, still showed every change (a component put, a
skeleton part's moved axis, a changed part), still re-solved mates driven by an
assembly global, and returned `False` while a component failed to rebuild. A
`Transform2` put alone marked nothing; an interference check marks the assembly,
reading component frames does not. SolidWorks 2026 (34.1.1) and 2024 SP5
(32.5.0). See
[assemblies/12](../entries/assemblies/12-rebuild-scope-and-the-save-flag.md).
