---
id: G49
title: Deleting a composite curve deletes the loft built on it
always: false
members: []
languages: [all]
---

A loft whose profile is a composite curve goes with the composite: delete the
composite and the loft is deleted too, not left with a dangling reference.
Changing which curves an existing composite joins was no way out either;
editing its sources could not be made to work. So when a composite's pieces
change, rename the old one aside (it keeps holding up the loft), make a new one
under the old name, and tell the user to re-pick it in the loft. Profiles must
also be cut into the same number of pieces: a three-piece composite lofted only
to another three-piece composite. SolidWorks 2026. See
[curves/06](../entries/curves/06-composite-curve.md).
