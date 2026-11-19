---
id: G47
title: Mirroring a body: the body goes at mark 256, and a wrong mark returns `None`
always: false
members: [IFeatureManager.InsertMirrorFeature2, IBody2.Select2, ISelectionMgr.CreateSelectData]
languages: [all]
---

`IFeatureManager.InsertMirrorFeature2(True, False, True, False, 0)` with the
plane at mark 2 and the body at mark 1 returned `None` and made nothing; so did
body and plane both at mark 1. With the body at **mark 256** and the plane at
mark 2 it made one `MirrorSolid` body of twice the volume, centred on the plane.
The body is selected through `IBody2.Select2(True, data)` with the mark set on
an `ISelectionMgr.CreateSelectData` object, so there is no mark argument to
notice. SolidWorks 2026 (revision 34.0.0), runs 20260915-002812 and
20260915-023929. See [features/11](../entries/features/11-mirror-body.md).
