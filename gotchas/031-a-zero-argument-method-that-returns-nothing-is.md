---
id: G31
title: A zero-argument method that returns nothing is not called by `call`
always: false
members: [IAssemblyDoc.FixComponent]
languages: [pywin32]
---

The late-bound rule in §5 — reach a zero-argument member by attribute access —
fetched `IAssemblyDoc.FixComponent` as a Python `method` object and never ran
it. Nothing raised. The check after it passed anyway, because the first
component of an assembly is already fixed when it is inserted, which is how
this went unnoticed in a passing probe. Call such members with explicit
parentheses and check their effect: on a rerun, `asm.FixComponent()` on a free
second component returned `None` and its `IsFixed` went from `False` to `True`
(SolidWorks 2026, revision 34.0.0, run 20260914-183429; see
[assemblies/01](../entries/assemblies/01-new-assembly-and-insert-components.md)). That pywin32 exposes a zero-argument member
with a return value as a property and one without as a method is the likely
cause; it was not established. Two more of the family, and a test that catches
them without knowing the member, are in **§55**. See
[connect/02](../entries/connect/02-attach-from-python.md).
