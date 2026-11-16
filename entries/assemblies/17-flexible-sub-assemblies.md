---
id: assemblies-17-flexible-sub-assemblies
title: Read and set whether a sub-assembly solves as flexible, and check the mates inside it from the top
status: partly-verified
verified_on: SolidWorks 2024 SP5 (32.5.0), for reading and putting Solving, reading nested mates, and clearing a stuck warning; motion through a flexible sub-assembly was not demonstrated
language: [python]
api: [IComponent2.Solving, IComponent2.FirstFeature, IComponent2.GetChildren, IConfiguration.GetRootComponent3, IModelDocExtension.GetWhatsWrong, IModelDocExtension.GetWhatsWrongCount, IFeature.GetErrorCode2, IMateEntity2.ReferenceComponent, IComponent2.ReferencedConfiguration, IComponent2.Transform2]
keywords: [flexible sub-assembly, rigid sub-assembly, Solving, swComponentSolvingOption_e, swComponentFlexibleSolving, swComponentRigidSolving, make flexible from code, nested component, sub-assembly mates from the top assembly, What's Wrong sub-assembly, error 51 warning stuck, Reference, GetRootComponent3, GetChildren, nested Name2 path, mate between sub-assemblies, ReferencedConfiguration changed]
answers: "How do I make a sub-assembly flexible (or rigid) from code, check the mates inside it as the top assembly solves them, and clear a warning that sticks to it?"
---

# Flexible sub-assemblies from code

## What this is for

A top assembly holds sub-assemblies that must move inside it: a gearbox and a
differential whose shafts are linked by mates in the top assembly. For that the
sub-assemblies solve as **flexible**, which is a property of each component in
the top assembly. This entry is how that property was read and set, how the
mates inside a flexible sub-assembly were read as the top assembly solves them,
and what clearing a stuck warning on one did to its parts.

**Partly verified.** Everything below was observed on SolidWorks 2024 SP5, but
turning a mechanism *through* a flexible sub-assembly from code was never
achieved: the one attempt to key two parts in different flexible
sub-assemblies together failed ([below](#a-mate-between-parts-of-two-flexible-sub-assemblies)).

## Reading and setting `Solving`

`IComponent2.Solving` is `swComponentSolvingOption_e`: **0 rigid, 1
flexible** (`swComponentRigidSolving`, `swComponentFlexibleSolving`, read from
`swconst.tlb`). Read by attribute access on each top-level component, it gave
0 for a part and for one sub-assembly, and 1 for three sub-assemblies.

Set by plain assignment, from the script that ran (names replaced by
placeholders):

```python
NAME = sys.argv[3] if len(sys.argv) > 3 else "SubB-1"
c = [x for x in ch.GetComponents(True) if x.Name2 == NAME][0]
print("before:", whats_wrong(ch) or "none", "| solving", c.Solving, "| ref", c.ReferencedConfiguration)
swcom._put(c, "Solving", 0); ch.EditRebuild3
c = [x for x in ch.GetComponents(True) if x.Name2 == NAME][0]
print("rigid:", whats_wrong(ch) or "none", "| solving", c.Solving)
swcom._put(c, "Solving", 1); ch.EditRebuild3
c = [x for x in ch.GetComponents(True) if x.Name2 == NAME][0]
print("flexible again:", whats_wrong(ch) or "none", "| solving", c.Solving, "| ref", c.ReferencedConfiguration, "| mate errors", errors(ch) or "none")
```

`swcom._put(obj, name, value)` is `setattr(obj, name, value)` with its COM
error turned into a sentence. The put read back 0 and then 1 on a component
fetched again after each rebuild. **SolidWorks 2024's `sldworks.tlb` lists
`IComponent2.Solving` as a get only** (`invkind` 2); the put through pywin32's
dynamic dispatch ran anyway and changed what the assembly did, as below.

`whats_wrong` is the `GetWhatsWrong` reader of
[assemblies/02](02-mates-from-code.md#when-a-mate-is-refused-or-over-defines),
with three `VARIANT(VT_BYREF | VT_VARIANT, None)` outs; `errors` reads every
mate's `GetErrorCode2` ([assemblies/15](15-free-a-rotation-without-moving-anything.md#the-calls)).

## The mates inside a sub-assembly, as the top assembly solves them

A sub-assembly component answers `FirstFeature`, and its `MateGroup` walks
like a document's:

```python
for c in ch.GetComponents(True):
    if not c.GetPathName.lower().endswith(".sldasm"): continue
    f = c.FirstFeature; bad = []; n = 0
    while f is not None:
        if f.GetTypeName2 == "MateGroup":
            s = f.GetFirstSubFeature
            while s is not None:
                n += 1
                w = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, False)
                code = s.GetErrorCode2(w)
                if code or w.value: bad.append((s.Name, code, w.value))
                s = s.GetNextSubFeature
        f = f.GetNextFeature
    print(f"{c.Name2:28} solving {c.Solving} mates read {n} | flagged {bad or 'none'}")
```

It read 41, 23, 17 and 17 mates for four sub-assemblies; the first three
counts are what the same walk gave on those sub-assemblies' own documents (the
fourth's was not read). **The flags differed from the sub-assembly's
own document**: through the component, seven of one flexible sub-assembly's 23
mates (four coincident mates and its three gear mates) read `GetErrorCode2` 51
with the warning flag `True`, while that sub-assembly's own document, open in
its own window, read What's Wrong 0 and no mate error.

At every level, components were reached from the active configuration's root:

```python
def all_comps(asm):
    """Every component at every level, keyed by the path of Name2s ('Sub-1/Comp-1')."""
    res = {}
    def walk(c, pre):
        for ch in c.GetChildren or ():
            k = pre + ch.Name2.split("/")[-1]
            res[k] = ch
            walk(ch, k + "/")
    root = asm.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    walk(root, "")
    return res
```

A nested component's `Name2` carries its parent's path: a mate entity's
`IMateEntity2.ReferenceComponent.Name2` in the top assembly read
`SubA-1/Hub-1`.

## A warning that stuck, and what clearing it did

After failed mate attempts in the top assembly had been deleted
([assemblies/15](15-free-a-rotation-without-moving-anything.md#why-it-is-not-obvious)),
the top assembly's What's Wrong kept one entry: the flexible sub-assembly's
component, code 51, warning `True`. (Earlier in the session the same list had
named another sub-assembly component, `GetTypeName2` `"Reference"`, code 51,
warning `True`.) No mate of the top assembly was in error.

- `ForceRebuild3(True)` on the top assembly returned `True` and left the entry.
- `Solving` put to 0 and `EditRebuild3`: What's Wrong empty.
- Put back to 1 and `EditRebuild3`: still empty, no mate error, and every
  nested mate read clean through the component.
- **But the flexible sub-assembly's parts had re-solved.** Against a record
  taken before, three of its parts had turned 175.8907° about Z, one 64.1093°,
  and two others had moved without turning about Z (their `ArrayData` up to
  1.49 off). Putting each nested component's recorded `Transform2` back
  through the `all_comps` handles, then `EditRebuild3`, restored them, with
  What's Wrong still empty.

So toggling `Solving` clears the stuck entry, at the price of the parts'
positions; record them first. On SolidWorks 2024 a 51 warning on gear-linked
mates is often not a real error ([GOTCHAS §118](../../GOTCHAS.md)).

## A mate between parts of two flexible sub-assemblies

Two gear mates already in the top assembly, made by hand, each joined a part
inside one flexible sub-assembly to a part inside another; both read clean,
1 : 1 (`GearRatioNumerator` and `GearRatioDenominator` both 0.001, the ratio as
typed, in metres), `Reverse` `True`, both entities' `EntityParams` directions
+Z. By the read-back rule of
[assemblies/10](10-mate-a-gear-train-that-turns.md#checking-a-gear-mates-sense-after-making-it)
(collinear, external) they turn their parts together. Neither was driven, so
that is a reading, not a motion test.

Adding an **angle mate** in the top assembly between a part of one flexible
sub-assembly and a part of the other, at their current angle, failed: the
first alignment and flip moved seven components, and the other eleven left the
new mate and two coincident mates at 51 (warning `True`). Every attempt was
deleted and the components put back.

## What it does not do

- Motion through a flexible sub-assembly was never shown from code; neither
  the drag operator nor a drive mate was tried across one.
- Making a sub-assembly flexible for the first time (from 0 to 1 where it had
  always been rigid) was not separately tested; the put was a toggle on one
  already flexible.
- **Unexplained:** between two reads a few minutes apart, the top assembly's
  `ReferencedConfiguration` for the *other* flexible sub-assembly changed from
  one of its configuration names to another; no script set it. The scripts in
  between toggled the first sub-assembly's `Solving` and put its parts back,
  while that other sub-assembly's own document had been switched between its
  configurations earlier. Read `ReferencedConfiguration` before relying on a
  flexible sub-assembly's state.
- Why a warning reads on the nested mates through the component and not in
  the sub-assembly's own document was not looked into.

## Evidence

SolidWorks 2024 SP5 (`RevisionNumber` 32.5.0), 2026-11-16, Python 3.13 with
pywin32 late binding, launched from WSL. A top assembly with a part and four
sub-assemblies (a planetary gearbox and three bevel differentials). From the
output, names replaced:

```
SubA-1      solving 1 mates read 41 | flagged none
SubB-1      solving 1 mates read 23 | flagged [('Coincident3', 51, True), ('Coincident6', 51, True), ('Coincident8', 51, True), ('Coincident10', 51, True), ('GearMate1', 51, True), ('GearMate2', 51, True), ('GearMate3', 51, True)]
SubC-1      solving 1 mates read 17 | flagged none
SubD-1      solving 0 mates read 17 | flagged none
before: [('SubB-1', 51, True)]
ForceRebuild3(True) -> True
after: [('SubB-1', 51, True)] | mate errors none
before: [('SubB-1', 51, True)] | solving 1 | ref Open
rigid: none | solving 0
flexible again: none | solving 1 | ref Open | mate errors none
  SubB-1/Collar-1    off 1.998e+00 turnZ  175.8907 shift 0.0000
  SubB-1/Spider-1    off 1.488e+00 turnZ   -0.0000 shift 0.0000
  SubB-1/Hub-1       off 1.963e+00 turnZ  175.8907 shift 0.0000
  SubB-1/Side-1      off 1.963e+00 turnZ  175.8907 shift 0.0000
  SubB-1/SideF-2     off 9.029e-01 turnZ   64.1093 shift 0.0000
  SubB-1/Spider-2    off 1.300e+00 turnZ    0.0000 shift 0.0000
SubB-1      solving 1 mates read 23 | flagged none
```

and after the puts, `what's wrong none | mate errors none`. The hand-made
cross-sub-assembly gear mates: `GearMate1 type 10 err 0 warn False ratio
0.001:0.001 Reverse True`, entities `('SubA-1/Hub-1', [0, 0, 1], …)` and
`('SubB-1/Carrier-1', [0, 0, 1], …)`.

## See also

- [assemblies/02 — Mates from code](02-mates-from-code.md) — `GetWhatsWrong` and its three outs
- [assemblies/05 — Test motion with the drag operator](05-test-motion-with-the-drag-operator.md)
- [assemblies/06 — Read every mate](06-read-every-mate.md) — the mate walk and the gear ratio as typed
- [assemblies/15 — Free a rotation without moving anything](15-free-a-rotation-without-moving-anything.md) — the keying mate that worked inside one assembly
- [assemblies/16 — Turn a mechanism with a temporary drive](16-turn-a-mechanism-with-a-temporary-drive.md) — recording and putting back positions
- [GOTCHAS §118](../../GOTCHAS.md)
