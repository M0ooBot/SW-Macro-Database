---
id: G6
title: The Running Object Table hands back an `IUnknown`
always: false
members: []
languages: [pywin32, late-bound]
---

Late binding cannot ask it for type information until it has been asked for
its `IDispatch` face:

```python
_dynamic.Dispatch(raw.QueryInterface(pythoncom.IID_IDispatch))
```
