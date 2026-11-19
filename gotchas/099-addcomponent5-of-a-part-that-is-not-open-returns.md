---
id: G99
title: `AddComponent5` of a part that is not open returns `None`
always: false
members: [AddComponent5, OpenDoc6]
languages: [all]
---

A part saved and closed, inserted by path, gave `None`: no error, no component.
Opened by `OpenDoc6` first, the same part went in. A part of the same file name
from another folder cannot be opened beside it at all (`OpenDoc6` error 65536,
`swFileWithSameTitleAlreadyOpen`). SolidWorks 2026 (34.0.0, 34.1.1) and 2024
SP5. See
[assemblies/01](../entries/assemblies/01-new-assembly-and-insert-components.md#inserting-a-part-that-is-not-open-and-two-parts-of-one-file-name).
