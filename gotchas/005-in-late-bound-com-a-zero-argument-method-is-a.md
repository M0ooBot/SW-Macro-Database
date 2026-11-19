---
id: G5
title: In late-bound COM, a zero-argument method is a property get
always: false
members: [RevisionNumber, ActiveDoc, IAssemblyDoc.FixComponent, IBody2.GetEdges, IFace2.GetTessTriangles]
languages: [pywin32, late-bound]
---

In Python with `win32com.client.dynamic`, `RevisionNumber` comes back as a
string just by attribute access, and `ActiveDoc` comes back as a document.
*Invoking* either raises "Member not found". Testing `callable()` does not save
you, because a member returning a document is itself callable.

The rule that works: call only members that take arguments.

```python
def call(obj, name, *args):
    member = getattr(obj, name)
    return member(*args) if args else member
```

**It has an exception.** A zero-argument member that *returns nothing* is not
invoked by attribute access: `IAssemblyDoc.FixComponent` came back as a Python
`method` object and never ran. Called with parentheses, `asm.FixComponent()`,
it ran and worked. So does a member returning an **array**: `IBody2.GetEdges`
and `IFace2.GetTessTriangles` both come back as uncalled methods. See §31 for
the first case and **§55 for the rule that covers all of them**.
