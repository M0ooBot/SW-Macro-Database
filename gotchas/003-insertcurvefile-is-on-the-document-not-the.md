---
id: G3
title: `InsertCurveFile` is on the document, not the feature manager
always: false
members: [InsertCurveFile]
languages: [all]
---

Calling it on `IFeatureManager` raises **error 438, object doesn't support
this property or method**, which reads like the method does not exist. It
does. It is on `IModelDoc2`.
