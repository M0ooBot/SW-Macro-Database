---
id: G39
title: `IMathUtility.CreateTransform` is "Member not found" to late binding
always: false
members: [IMathUtility.CreateTransform, IMathUtility.CreatePoint]
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

`IMathUtility.CreatePoint` fails as well under late binding, with a different
error. On SolidWorks 2024 SP5 (32.5.0),
`utility.CreatePoint(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [x, y, z]))`
from pywin32's dynamic dispatch raised `com_error` **-2147417851** (0x80010105,
"The server threw an exception"). It was raised inside pywin32's `__getattr__`,
which fetches the member as a property get before the arguments are applied.
The `DISPATCH_METHOD` route above was **not tried** on `CreatePoint`. The
run transformed the point by hand instead, from the component's
`Transform2.ArrayData` with the rotation stored by columns
([§10](010-a-transform-s-rotation-is-stored-by-columns.md)). With `a` the 16
doubles, rotation `r = a[0:9]`, translation `t = a[9:12]` and scale
`s = a[12]`:
`x' = s·(x·r0 + y·r3 + z·r6) + t0`, `y' = s·(x·r1 + y·r4 + z·r7) + t1`,
`z' = s·(x·r2 + y·r5 + z·r8) + t2`, all in metres.
