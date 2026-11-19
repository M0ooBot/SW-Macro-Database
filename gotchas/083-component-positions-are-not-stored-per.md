---
id: G83
title: Component positions are not stored per configuration
always: false
members: [AddMate5, Transform2]
languages: [all]
---

A configuration stores suppression, not where free components sit. Two
configurations whose only difference was where a part had been dragged showed
the same position. Each configuration needs its own mates that fix the position
**uniquely** and do not fight the rest: distances to planes beside an existing
limit mate, a second limit mate, and a target point 0.001 mm off the pin's circle
all added with `AddMate5` error 5 and put mates at error 51; the moving axis
coincident with an *exact* point in an assembly sketch solved in every
configuration. SolidWorks 2024 SP5 (32.5.0). See
[assemblies/07](../entries/assemblies/07-configurations-that-hold-different-positions.md).

**Qualified by a later measurement that found the opposite under another
procedure.** On SolidWorks 2026 (34.1.1) and 2024 SP5, a component held by an
axis mate and a distance along it, turned by a `Transform2` put in one
configuration and followed by a top-only rebuild (`ForceRebuild3(True)`), held
its own turn in each configuration, read through freshly fetched handles, and
kept it through a save and reopen; a put held in the active configuration only.
The clean case is the component with no gear mate. A second component, whose
gear mate was suppressed in the configuration of the put and on in the other,
came back to its old turn in the other configuration too, but there its gear
mate re-solved, so its result is consistent with positions kept per
configuration, not proof of it. The drag sentence above records neither how
the positions were set nor how they were read; the instrumented reads in
assemblies/07 (show, then `ForceRebuild3(False)`) were of mates per
configuration, and its one instrumented "same position" was of an attempt
whose mates were in error (51). Not tried, so neither statement is known to
reach the other's case: a drag instead of a put; a full rebuild (`ForceRebuild3(False)`) after a show; a put on a component whose gear mate is on in every configuration; a component free to slide as well as turn. Stale handles do not explain the later
result: a stale handle answers `Transform2` with None, not an old position. See
[assemblies/13](../entries/assemblies/13-assembly-configurations-from-code.md#where-components-stand-in-each-configuration).
