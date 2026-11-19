---
id: G71
title: Zeroing an appearance's transparency does not make the part look like the others
always: false
members: [GetRenderMaterialsCount2]
languages: [all]
---

A part whose every body drew see-through had a `color.p2m` appearance applied
to the whole part, at transparency 0.75. With the transparency set to 0 in
SolidWorks the part still looked glossy and unlike the user's other parts.
Those parts had **no applied appearance at all**, and the odd one's carried
reflectivity 0.15. Removing the appearance, rather than editing it, gave the
same values as the other parts. Compare `GetRenderMaterialsCount2` on a part
that looks right before editing anything. SolidWorks 2024 SP5 (32.5.0). See
[appearance/01](../entries/appearance/01-read-and-remove-a-part-appearance.md).
