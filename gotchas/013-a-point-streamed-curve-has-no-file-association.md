---
id: G13
title: A point-streamed curve has no file association
always: false
members: [InsertCurveFileBegin, LoadPointsFromFile]
languages: [all]
---

If you created a curve with `InsertCurveFileBegin`/`Point`/`End` rather than
from a file, it carries no path, so the 2025 Reload button has nothing to
reload from. It can still be refreshed with `LoadPointsFromFile` afterwards,
which was tested and works, but the dialog route is closed to it.
