---
id: G4
title: A bare `None` is a type mismatch for an absent COM object
always: false
members: [ModifyDefinition, GetObjectByPersistReference3]
languages: [pywin32]
---

`ModifyDefinition(data, doc, component)` takes a component, which a part does
not have. In Python, passing `None` fails. It needs a typed null:

```python
VARIANT(pythoncom.VT_DISPATCH, None)
```

`GetObjectByPersistReference3` has the same shape of problem in the other
direction: an out parameter that must be supplied as a by-reference integer,
`VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)`. Both are silent until they
are not. See [connect/02](../entries/connect/02-attach-from-python.md).
