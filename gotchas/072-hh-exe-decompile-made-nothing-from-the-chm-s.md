---
id: G72
title: `hh.exe -decompile` made nothing from the `.chm`'s install path, and said nothing
always: false
members: []
languages: [all]
---

Unpacking `sldworksapi.chm` from
`C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS (2)\api\` gave an empty output
folder three ways, with no error. Copied to `%TEMP%\swapi.chm` first, it
unpacked to 17,392 files. The spaces and brackets in the install path are
the likely cause, being the one thing that changed; that was not isolated
further. Count the files afterwards; an empty folder is the only sign. See
[connect/12](../entries/connect/12-read-the-api-help-offline.md).
