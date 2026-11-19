---
id: G51
title: Clearing the selection during a user's pick crashed SolidWorks
always: false
members: [IModelDoc2.ClearSelection2]
languages: [all]
---

A tool polling the selection and clearing it after each read
(`IModelDoc2.ClearSelection2(True)`), so that each click was an event, crashed
SolidWorks 2026 twice on 2026-09-16: an access violation in SolidWorks' own
`ClearSelectionsNotify`, while the user was in a sketch with the Point property
page open on the point just clicked. The read and the clear were the last API
calls both times. Read the selection only, tell clicks apart by the selection
changing, and refuse to start anything that selects while
`ISketchManager.ActiveSketch` is not `None`. See
[reading/04](../entries/reading/04-read-the-selection.md), which recommended the
clear until this.
