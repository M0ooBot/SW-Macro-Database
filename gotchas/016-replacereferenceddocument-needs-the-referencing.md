---
id: G16
title: `ReplaceReferencedDocument` needs the referencing documents closed
always: false
members: [ReplaceReferencedDocument]
languages: [all]
---

Check with `GetOpenDocumentByName` and ask the user to close first, rather than
failing halfway through a batch.
