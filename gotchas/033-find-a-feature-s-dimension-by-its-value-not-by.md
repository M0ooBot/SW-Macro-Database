---
id: G33
title: Find a feature's dimension by its value, not by name or position
always: false
members: []
languages: [all]
---

A circular pattern's dimensions came back as `[D3 = 2π, D1 = count]`: the
count second, the angle first. An extrusion's came back as its own depth `D1`
**and** its sketch's `OD`. Code that takes the first dimension, or assumes
`D1` is the one it wants, relies on an order and a naming nothing promises.
Match the value you asked for, refuse if more than one matches, then rename it.
See [features/04](../entries/features/04-read-a-features-dimensions.md).
