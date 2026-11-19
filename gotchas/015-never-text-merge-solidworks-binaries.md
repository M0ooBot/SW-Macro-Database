---
id: G15
title: Never text-merge SolidWorks binaries
always: false
members: []
languages: [all]
---

Part, assembly and drawing files are opaque binaries. In git, mark them binary
and track them with LFS. Conflicts get prevented with file locks, not resolved.

**LFS is not free, and generated parts blow through it.** Writing one file per
configuration turns a 9-part folder into 315 files, and a whole library into a
few thousand. That is ordinary storage but an expensive LFS quota. A nested
`.gitattributes` in the generated folder can opt those files back out to plain
blobs while the hand-built masters above it stay in LFS.
As of 2026 the container format also cannot be parsed for references directly,
and the Document Manager API that would do it is behind a subscription licence.
The regular API is the way in. See
[reading/01](../entries/reading/01-dependencies-of-a-closed-file.md).
