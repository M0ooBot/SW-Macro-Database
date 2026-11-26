---
id: G117
title: A concentric mate with Lock rotation set stops the part turning, and a mate dump that skips it looks clean
always: false
members: [IConcentricMateFeatureData.LockRotation, IAssemblyDoc.AddMate5]
languages: [all]
---

A concentric mate can carry **Lock rotation** (the check box in its
PropertyManager). The part then cannot turn about that axis, and nothing in the
tree says so: the feature is still `MateConcentric`, `IMate2.Type` 1, error code
0. The walk in [assemblies/06](../entries/assemblies/06-read-every-mate.md) does
not try `LockRotation`, so its dump shows such a mate as answering only
`MateAlignment`, and a reader concludes the part is free to spin.

What it looked like on SolidWorks 2024 SP5 (32.5.0): a shaft with a D flat sat
in a bore with a matching flat, the two flats about 120° apart around the axis.
The shaft was held to the bore by a concentric with Lock rotation set (the shaft
in one flexible sub-assembly, the bore in another, the concentric at the top
level). A parallel mate (`AddMate5` type 3) between the two flats, with
alignment 2 and again with 1, returned status 1 and moved nothing. After
`ForceRebuild3(True)`, the new mate and the locked concentric read
`GetErrorCode2` 51, and `GetWhatsWrongCount` read 6. The `EditRebuild3` run
right after the first add had left every code at 0. Only the forced rebuild
showed the errors. An angle mate (type 6) set to the flats' **current** angle
returned status 5 (over-defined), with 51 on it and on the concentric. Deleting
the added mate brought every code back to 0. Unticking Lock rotation was the fix.

**The tell:** a mate that asks for the position the part is already in is
refused as over-defined. The freedom it would take is already taken. Before
suspecting the solver, read `LockRotation` on every `MateConcentric` that
touches the part:

```python
d = call(f, "GetDefinition")             # f: a MateConcentric feature
lock = getattr(d, "LockRotation", "?")
```

See [assemblies/06](../entries/assemblies/06-read-every-mate.md#a-concentrics-lock-rotation)
for the run.
