---
id: G17
title: `check-ignore` and other verifications that read what you control
always: false
members: []
languages: [all]
---

Not a SolidWorks issue, but it bites automation work generally: a verification
that reads a surface the thing under test controls is not a verification. When
checking what is committed, read the committed object, not the working tree.
