---
schema: 2
id: assemblies-14-in-context-part-across-configurations
title: Show an in-context part at a different size in each assembly configuration
answers: "My in-context part (a spring whose length follows the parts around it) draws at the same size in every configuration's drawing view. How do I make each assembly configuration keep its own size?"
keywords: [in-context, virtual component, external reference, spring length, configuration specific geometry, same size in every view, drawing view wrong size, ReferencedConfiguration, part configuration, equation driven by in-context dimension, sweep lost body, GetFaceCount 0]
api: [IConfigurationManager.AddConfiguration2, IComponent2.ReferencedConfiguration, IComponent2.GetModelDoc2, IModelDoc2.GetConfigurationNames, IModelDoc2.Parameter, IFeature.GetFaceCount, IComponent2.GetBodies2]
language: [python]
status: verified
verified_on: SolidWorks 2024 SP5 (32.5.0)
majors: [32]
evidence: []
recipe_status: null
recipe_evidence: []
superseded_by: null
---

# Show an in-context part at a different size in each assembly configuration

## What this is for

A part modelled in context, such as a spring whose helix height is driven by an
equation from a reference dimension that measures the gap between two other
parts. It follows the mechanism live. But on a drawing with one view per
assembly configuration (button up, button down), every view drew the spring at
the **same** length: whichever the last rebuild produced. In-context
geometry is not per assembly configuration.

Attach as in [assemblies/06](06-read-every-mate.md#attaching). The position
configurations themselves are
[assemblies/07](07-configurations-that-hold-different-positions.md).

## The fix: one part configuration per assembly state

A part stores its geometry **per part configuration**. So give the in-context
part a configuration for each state, point each assembly configuration's
component at its own, and rebuild each assembly configuration once:

```python
c = comp("<part prefix>"); m = call(c, "GetModelDoc2"); pcm = call(m, "ConfigurationManager")
for n in ("Rest", "Pressed"):
    if n not in call(m, "GetConfigurationNames"): pcm.AddConfiguration2(n, "", "", 0, "", "", False)
try: m.ShowConfiguration2("Default")
except Exception: pass
MAP = {"Default": "Default", "Position A": "Rest", "Position B": "Pressed", "Exploded": "Rest"}
for acfg, pcfg in MAP.items():
    show(asm, acfg); cc = comp("<part prefix>"); cc.ReferencedConfiguration = pcfg
    try: asm.ForceRebuild3(False)
    except Exception: pass
```

`comp(prefix)` finds the assembly component whose `Name2` starts with the
prefix; `show` switches configuration and rebuilds
([assemblies/07](07-configurations-that-hold-different-positions.md#showconfiguration2-and-forcerebuild3-can-raise-and-still-succeed)).
`IComponent2.ReferencedConfiguration` is put while that assembly configuration
is active, and applies to it.

When the assembly rebuilds in a configuration, the in-context reference and the
equation update the **referenced** part configuration and leave the others as
they were. Two section views of two assembly configurations then drew two
spring lengths. The equation stays as it was, so the part's `Default`, mapped to
the assembly's `Default`, still follows the mechanism live.

## Why it is not obvious

- **Nothing reports the problem.** Each view's `ReferencedConfiguration` is
  right and the positions of the other parts are right. Only the in-context
  part is wrong, and only in a picture.
- **Reading the size back from the part misleads.**
  `call(m.Parameter("D3@Helix/Spiral1"), "SystemValue")` on the part document
  read the same height in every assembly configuration, because it reports the
  part's own active configuration. The drawing showed the heights were
  different. Check the picture.
- `AddConfiguration2(name, "", "", 0, "", "", False)` on the part left the
  **new** configuration active, despite the last argument. Switch the part back
  with `ShowConfiguration2` before going on.
- **The equation cannot be made configuration-specific from code** on such a
  part. Every equation call returned −1, and `Delete` removed the equation
  ([equations/01](../equations/01-global-variables-from-code.md#on-a-virtual-in-context-part)).
  The fix above needs no change to the equation.

## What it does not do

- **Open: a body that disappeared.** Once, after a sequence that included a mate
  added with stale references and then deleted
  ([assemblies/07](07-configurations-that-hold-different-positions.md#read-the-entities-after-switching-configuration)),
  configuration switches and a save, the in-context part's sweep had
  **no faces** (`IFeature.GetFaceCount` 0, `IComponent2.GetBodies2(0)` empty)
  and reported **no error**. Rebuilding did not bring it back. Restoring the
  assembly file from before the session and repeating the steps one at a time,
  checking the face count after each, never reproduced it. Check
  `GetFaceCount` on such a part after any batch of changes and before saving;
  keep a copy of the assembly to go back to.
- Parts with more than one in-context feature, and in-context references to
  parts that are themselves suppressed in a configuration, were not tried.

## Evidence

SolidWorks 2024 SP5 (`RevisionNumber` 32.5.0), 2026-11-15. A virtual spring (helix
and sweep, height from an equation on an in-context reference dimension) in an
assembly with four configurations, two of which hold a sliding part at opposite
ends of its travel. Before the fix, two section views of those configurations
drew the same spring length in the exported PDF. After adding two part
configurations and mapping them, the views drew an extended and a compressed
spring; every assembly configuration read `GetBodies2(0)` with one body and
`ReferencedConfiguration` as mapped; the assembly saved and reopened with the
same state. Names are placeholders here.

## See also

- [assemblies/07 — Configurations that hold different positions](07-configurations-that-hold-different-positions.md)
- [drawings/06 — Alternate position views](../drawings/06-alternate-position-views.md) — a view can draw another configuration's pose
- [drawings/08 — Section views from code](../drawings/08-section-views-from-code.md)
- [equations/01 — Global variables from code](../equations/01-global-variables-from-code.md)
- [GOTCHAS §115, §116](../../GOTCHAS.md)
