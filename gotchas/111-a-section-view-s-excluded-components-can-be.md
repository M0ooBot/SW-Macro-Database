---
id: G111
title: A section view's excluded components can be ignored at creation
always: false
members: [CreateSectionViewAt5, IView.GetSection, SetExcludedComponents]
languages: [all]
---

`CreateSectionViewAt5`'s excluded-components array left the parts hatched on a
four-configuration assembly, under every option tried. Passing the same array
afterwards to `IView.GetSection`'s `SetExcludedComponents`, through `Invoke`
because late binding sees it as a property, worked. SolidWorks 2024 SP5
(32.5.0). See
[drawings/08](../entries/drawings/08-section-views-from-code.md#excluding-components-after-the-fact-idrsectionsetexcludedcomponents).
