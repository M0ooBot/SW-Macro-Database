---
id: G10
title: A transform's rotation is stored by columns
always: false
members: [IMathTransform.ArrayData]
languages: [all]
---

`IMathTransform.ArrayData` is sixteen doubles: nine of rotation, three of
translation, then a scale. The first three are where the local X axis ends up,
the next three the local Y, the next three the local Z.

Reading them as rows transposes the rotation. This is **silent on the Front
plane**, whose transform is the identity, and wrong everywhere else. The
symptom was the Top plane reporting a normal of −Y and the Right plane −X. See
[reading/05](../entries/reading/05-sketch-to-model-transform.md).
