---
id: G39
title: `IMathUtility.CreateTransform` is "Member not found" to late binding
always: false
members: [IMathUtility.CreateTransform]
languages: [pywin32, late-bound]
---

From pywin32's dynamic dispatch, `CreateTransform(data)` raised
**`DISP_E_MEMBERNOTFOUND`** with a Python list and with a
`VARIANT(VT_ARRAY | VT_R8, data)` alike, which reads as though the member does
not exist. Invoking the same dispid with `pythoncom.DISPATCH_METHOD` and the
typed array made the transform:

```python
oleobj = utility._oleobj_
raw = oleobj.Invoke(oleobj.GetIDsOfNames("CreateTransform"), 0, pythoncom.DISPATCH_METHOD, True,
                    VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, data))
```

The probe's reading is that late binding asked for a property get with an
argument; that was not isolated. Put the result on `IComponent2.Transform2` by
plain assignment, with the rotation **by columns** (§10), and read it back.
SolidWorks 2026 (revision 34.0.0). See
[assemblies/04](../entries/assemblies/04-mates-between-non-parallel-axes.md).
