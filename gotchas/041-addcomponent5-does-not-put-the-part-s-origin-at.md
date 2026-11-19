---
id: G41
title: `AddComponent5` does not put the part's origin at the point you give
always: false
members: [AddComponent5]
languages: [all]
---

A 10 mm thick cylinder inserted at (60, 0, 0) mm read a translation of
(60.0, 0.0, −5.0) mm. Left where it landed and used as the reference for an
origin-to-origin mate, it put the mated component's origin 5.0 mm from where
its frame said, with the rotation exact. The probe's reading is that the
part's middle goes at the point; only that one part thickness was tried, so
the rule is not established. What worked either way: set **every**
component's frame with `Transform2`, the first included, before mating.
SolidWorks 2026 (revision 34.0.0). See
[assemblies/04](../entries/assemblies/04-mates-between-non-parallel-axes.md) and
[assemblies/01](../entries/assemblies/01-new-assembly-and-insert-components.md).
