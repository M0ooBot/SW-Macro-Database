---
id: G2
title: The API is in metres, always
always: true
members: []
languages: [all]
---

The file format takes a `mm` suffix and honours it. The API does not take
units at all: everything is metres, whatever the document is set to.

Recording the import dialog proved both halves at once. A file written as
`-50.000000mm` came back as:

```vb
boolstatus = Part.InsertCurveFilePoint(0, 0, -0.05)
```

Radians for angles, on the same principle. See
[sketches/05](../entries/sketches/05-units-and-number-format.md).
