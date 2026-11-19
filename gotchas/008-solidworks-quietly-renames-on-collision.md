---
id: G8
title: SolidWorks quietly renames on collision
always: true
members: [Name]
languages: [all]
---

Set `feature.Name = "S9"` when an `S9` already exists and you get `S91` or
similar, with no error. A record holding a name that does not exist is a
silent failure. **Always read the name back:**

```python
feature.Name = new
return str(call(feature, "Name"))
```
