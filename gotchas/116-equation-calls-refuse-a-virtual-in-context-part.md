---
id: G116
title: Equation calls refuse a virtual in-context part, but `Delete` does not
always: false
members: [Delete, Add2, Add3, SetEquationAndConfigurationOption]
languages: [all]
---

On a virtual in-context part with several configurations, `Add2`, `Add3` and
`SetEquationAndConfigurationOption` all returned −1; `Delete(0)` returned 0 and
removed the equation for good. Close without saving to get it back. Never delete
before an add has worked on that document. SolidWorks 2024 SP5 (32.5.0). See
[equations/01](../entries/equations/01-global-variables-from-code.md#on-a-virtual-in-context-part).
