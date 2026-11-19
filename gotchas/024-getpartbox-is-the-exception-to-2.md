---
id: G24
title: `GetPartBox` is the exception to §2
always: false
members: [IPartDoc.GetPartBox]
languages: [all]
---

The API is in metres everywhere, except that `IPartDoc.GetPartBox` takes a
boolean that decides. `GetPartBox(true)` is metres. `GetPartBox(false)` converts
to **the document's own unit system**, so the same call returns different
numbers for two parts depending on how each file was set up.

Pass `true` and convert yourself, particularly when the result is a check. A
verification that silently depends on a setting in the file being verified is
not a verification — which is §17, arriving from a different direction.

See [reading/09](../entries/reading/09-bounding-box.md).
