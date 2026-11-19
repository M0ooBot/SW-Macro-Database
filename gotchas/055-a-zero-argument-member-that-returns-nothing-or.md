---
id: G55
title: A zero-argument member that returns nothing *or an array* comes back uncalled
always: false
members: [ReleaseSelectionAccess, IBody2.GetEdges, IFace2.GetTessTriangles, IAssemblyDoc.FixComponent, IMassProperty.AddBodies, IModelDocExtension.DeleteDisplayStateSpecificRenderMaterial, IModelDocExtension.CreateBalloonOptions, IEdge.GetCurveParams2, IModelDoc2.EditRebuild3, INote.GetBalloonStyle, IMeasure.Calculate, ISldWorks.ExitApp]
languages: [pywin32]
---

§5's rule — reach a zero-argument member by attribute access — and §31's
exception for `FixComponent` are the same fact seen twice. On SolidWorks 2026
it has a third and fourth case, and together they give the rule that works:

| Member | Attribute access gives | Symptom |
|---|---|---|
| composite feature data `ReleaseSelectionAccess` | an uncalled `method` | the tree silently stays rolled back |
| `IBody2.GetEdges` | an uncalled `method` | `TypeError: 'method' object is not iterable` |
| `IFace2.GetTessTriangles(True)` | an uncalled `method` | the same |
| `IAssemblyDoc.FixComponent` | an uncalled `method` | nothing happens (§31) |

A member that returns **nothing or an array** is handed over as a bound method;
a member that returns a value is invoked for you. A *value* never comes back
looking like a method object, so testing what came back is safe where testing
the member's name is not:

```python
member = getattr(obj, name)
if args:
    return member(*args)
if type(member).__name__ == "method":
    return member()
return member
```

Members observed **not** to need this on the same session: `GetFaces`,
`GetBody`, `GetCurve`, `GetCurveParams2`, `GetMassProperties`, `IsRolledBack`,
`Name`, `GetTypeName2`, `GetNextFeature`, `EditRebuild3` and
`InsertPlanarRefSurface` — the last two of which *do* something and still come
back as their result.

One case this does not cover: `IMassProperty.AddBodies` reached by `getattr`
answered a `bool` — it had already run, with no bodies — and then could not be
called with its bodies at all (`'bool' object is not callable`). Where a member
both takes arguments and might be exposed as a property, check the effect.
SolidWorks 2026 SP0.0. See [connect/02](../entries/connect/02-attach-from-python.md).

The same happened to `IModelDocExtension.DeleteDisplayStateSpecificRenderMaterial`
on SolidWorks 2024 SP5 (32.5.0): one argument-less run that deleted nothing,
then `'bool' object is not callable`. Invoking its dispid with
`pythoncom.DISPATCH_METHOD`, as in §39, made it take its arguments and work.
See [appearance/01](../entries/appearance/01-read-and-remove-a-part-appearance.md).


On SolidWorks 2024 SP5 (32.5.0), drawing work met more members that attribute
access had already run, where adding parentheses failed:
`IModelDocExtension.CreateBalloonOptions` ("Member not found"),
`IEdge.GetCurveParams2`, `IModelDoc2.EditRebuild3` and
`INote.GetBalloonStyle` (`'tuple'`/`'bool'`/`'int' object is not callable`). Reach them
through `call`. See [drawings/02](../entries/drawings/02-bom-table-and-balloons.md)
and [drawings/09](../entries/drawings/09-add-dimensions-and-tolerances.md).

`IMeasure.Calculate` is the same case, on SolidWorks 2026 (34.1.1): reached by
attribute access it answered a `bool`, and the call with its argument failed
with `'bool' object is not callable`. Invoked by its dispid with
`DISPATCH_METHOD` and a typed null dispatch it returned `True` and the measure
read the right distance, on 2026 and 2024 SP5. The failing form is recorded in
the probe's source, not in a kept result. See
[reading/16](../entries/reading/16-measure-between-two-selections.md).

`ISldWorks.ExitApp` is the plain case, and a pywin32 late-binding point rather
than a SolidWorks one: it returns nothing, so `call(app, "ExitApp")` only
fetched it and SolidWorks stayed open (seen once, on 2026, in a run whose
results were not kept); `app.ExitApp()` ended it, on 2026 (34.1.1) and 2024 SP5. See [`code/python/gear_train/`](../code/python/gear_train/README.md).
