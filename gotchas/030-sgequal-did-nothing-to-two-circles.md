---
id: G30
title: `sgEQUAL` did nothing to two circles
always: false
members: [sgEQUAL]
languages: [all]
---

Two circles of radius 4 and 7 mm, both selected, `sgEQUAL`: no error, and the
radii were still 4 and 7. `sgSAMELENGTH` on the same selection made them both
4. A relation that silently does nothing leaves a sketch that looks related and
is not; check relations by where the geometry went. See
[sketches/03](../entries/sketches/03-relation-constants.md).
