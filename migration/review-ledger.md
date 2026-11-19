# Review list: API ledger (step 5)

API-LEDGER.md is now generated from `api-ledger.json`, one row per call form as before; the
generated file was checked equal to the original before it was replaced. Each row gains a
status from the fixed set (verified, partly-verified, unverified, fails, absent), the cell's
own wording as `note`, the run it cites as `provenance`, `majors`, `members` and `interface`.
Flag only the rows you disagree with. Written by `tools/migrate.py ledger` from its
LEDGER_STATUS and LEDGER_MAJORS tables and the rules below.

## Status cells that needed a decision (13)

| Status cell (source) | Rows | Member | Chosen status | Majors | Why |
|---|---|---|---|---|---|
| “Observed once (the dialog), SW 2024 SP5 (32.5.0), 2026-11-02; the `0x80010105` verified, tier 7/8 2026-11-13/14” | 1 | `CloseDoc(title)` on an **assembly**, SW 2024 | **fails** | [32] | Both halves are failures seen (a hang on a dialog, once; the 0x80010105 exception), on 2024; the note keeps "observed once". |
| “Verified; crash observed, Airfoil Converter 2026-09-16” | 1 | `ClearSelection2(all)` | **verified** | [34] | The call works; the crash is a condition (a user's pick), which the note and purpose keep. Majors: The preamble: rows marked "Airfoil Converter 2026-09-16" come from that tool's work on SolidWorks 2026. |
| “Ran, SW 2024 (32.5.0), 2026-10-01” | 1 | `GraphicsRedraw2()` | **partly-verified** | [32] | It ran without error; whether it redraws (its purpose) was not observed. |
| “Read, SW 2024 (32.5.0), 2026-10-01” | 1 | `MaterialID` | **partly-verified** | [32] | It was read; what the value means is not known. |
| “Set, SW 2026 SP0.0, Airfoil Converter 2026-09-23” | 1 | `EnableGraphicsUpdate` | **partly-verified** | [34] | It was set; its effect on graphics was not observed, only that it did not speed a reload. |
| “Verified for 1 and 4, verified not to work for 2, SW 2026 SP0.0, Airfoil Converter 2026-09-22” | 1 | `EditRollback(action, featureName)` | **partly-verified** | [34] | Two actions work and one does not, for one call form: neither verified nor fails as a whole. |
| “Verified for item 3, SW 2026 SP0.0, Airfoil Converter 2026-09-22” | 1 | `GetMassProperties(1.0)` | **partly-verified** | [34] | One item of the twelve is identified; the rest were not. |
| “Verified on a line, SW 2026 (34.0.0)” | 1 | `ConstructionGeometry` | **partly-verified** | [34] | Verified on a line only; the purpose says other entities vary by version. |
| “Verified, SW 2024 SP5 (32.5.0), 2026-10-28 (read only)” | 1 | `Alignment`, `Flipped` | **partly-verified** | [32] | Read only, and the purpose says the meanings were not checked. |
| “Verified, SW 2024 SP5 (32.5.0), 2026-10-28 (value suspect)” | 1 | `MateAlignment` | **partly-verified** | [32] | The cell itself calls the value suspect. |
| “Verified, SW 2024 SP5 (32.5.0), 2026-11-09; exclusion not reproduced 2026-11-15” | 1 | `IDrawingDoc.CreateSectionViewAt5(x, y, 0, label, options, excludedComponents, 0)` | **partly-verified** | [32] | A later run found the exclusion array ignored (GOTCHAS §111), so part of the form is not reliable. |
| “Verified not to carry through gear or lock mates on that train, Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), tier 7/8 2026-11-13/14” | 1 | `BeginDrag` / `Drag(xform)` / `EndDrag`, the recipe above, on a gear train | **fails** | [32, 34] | Observed not to do what the row is about (carry a drag through the train). |
| “Verified absent, Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), tier 7/8 2026-11-13/14” | 1 | `AccessSelections` | **absent** | [32, 34] | Observed not to exist on both versions. |

## "Verified" and nothing more (28)

The source says verified and names no version or run. Proposed `verified`, `majors: []`,
`note: "no version recorded"`: the cell still reads "Verified", and SW-Agent's `api_status`
shows the note. Flag a row to have it downgraded instead.

| Section | Member | Purpose |
|---|---|---|
| ISldWorks (the application) | `ActiveDoc` | The document on screen, or `Nothing` |
| ISldWorks (the application) | `GetFirstDocument` | First of the open documents, walked with `GetNext` |
| ISldWorks (the application) | `Visible` | Show or hide a launched instance |
| ISldWorks (the application) | `GetDocumentDependencies2` | References of a **closed** file, without opening it |
| IModelDoc2 (a part, assembly or drawing) | `GetTitle` | Document name, used to match the part you want |
| IModelDoc2 (a part, assembly or drawing) | `GetNext` | Next open document |
| IModelDoc2 (a part, assembly or drawing) | `FirstFeature` | Head of the feature tree |
| IModelDoc2 (a part, assembly or drawing) | `ForceRebuild3(topOnly)` | Rebuild. Call once, after the last change |
| IModelDoc2 (a part, assembly or drawing) | `SelectionManager` | The selection, for reading what was clicked |
| IModelDoc2 (a part, assembly or drawing) | `Extension` | `IModelDocExtension`, below |
| IFeature | `Name` | Read and write. **Read it back after writing** |
| IFeature | `GetNextFeature` | Next sibling in the tree |
| IFeature | `GetTypeName2` | Type string, e.g. `"CurveInFile"`, `"CompositeCurve"` |
| IFeature | `GetSpecificFeature2` | The concrete feature behind a reference plane; on an `FtrFolder`, the `IFeatureFolder`; on a sketch feature, the `ISketch` |
| ISketchSegment / ISketchPoint | `X` / `Y` / `Z` | A sketch point's coordinates, in **sketch** space |
| ISelectionMgr | `GetSelectedObjectCount2(mark)` | How many things are selected. `-1` = any mark |
| ISelectionMgr | `GetSelectedObject6(index, mark)` | The selected object, 1-based |
| ISelectionMgr | `GetSelectedObjectType3(index, mark)` | A `swSelectType_e` number |
| ISelectionMgr | `GetSelectedObjectsSketch(index)` | The sketch a selected entity belongs to |
| Geometry interrogation | `GetPoint` | A point's coordinates, in metres |
| Geometry interrogation | `GetCurve` | The underlying curve |
| Geometry interrogation | `IsLine` | Whether it is straight |
| Geometry interrogation | `GetStartVertex` / `GetEndVertex` | An edge's ends |
| Geometry interrogation | `GetSurface` | The underlying surface |
| Geometry interrogation | `IsPlane` | Whether it is planar |
| Geometry interrogation | `PlaneParams` | Normal first, then a root point |
| Geometry interrogation | `Transform` → `ArrayData` | Sixteen doubles: rotation **by columns**, translation, scale |
| Geometry interrogation | `ModelToSketchTransform` → `Inverse` → `ArrayData` | Sketch space to model space |

## Every status cell, as read (rules)

Rules: "Verified not to work …" is `fails`; "Verified absent …" is `absent`; otherwise the
first words give the status. `majors` are the versions the cell names before any semicolon
(after it only when nothing before it names one); none for `unverified`. `provenance` is
what follows the last version named (the run), or `null`. `languages` is `[pywin32]` where the
cell says "from Python", else `[]` (the row does not say).

| Status cell (source) | Rows | Status | Majors | Provenance | Languages |
|---|---|---|---|---|---|
| “Verified, SW 2024 SP5 (32.5.0), 2026-10-30” | 76 | verified | [32] | “2026-10-30” | [] |
| “Verified, SW 2026 (34.0.0)” | 59 | verified | [34] | *(none)* | [] |
| “Verified, SW 2026 SP1.1” | 30 | verified | [34] | *(none)* | [] |
| “Verified” | 28 | verified | [] | *(none)* | [] |
| “Verified, SW 2026 SP0.0, Airfoil Converter 2026-09-22” | 26 | verified | [34] | “Airfoil Converter 2026-09-22” | [] |
| “Verified, SW 2026 (34.0.0, 34.1.1) and SW 2024 SP5 (32.5.0), tier 7/8 2026-11-13/14” | 23 | verified | [32, 34] | “tier 7/8 2026-11-13/14” | [] |
| “Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), tier 7/8 2026-11-13/14” | 22 | verified | [32, 34] | “tier 7/8 2026-11-13/14” | [] |
| “Verified, SW 2024 SP5 (32.5.0), 2026-11-09” | 19 | verified | [32] | “2026-11-09” | [] |
| “Unverified” | 18 | unverified | [] | *(none)* | [] |
| “Verified, SW 2026 (34.0.0), dev runs 2026-09-15” | 17 | verified | [34] | “dev runs 2026-09-15” | [] |
| “Verified, SW 2024 (32.5.0), 2026-10-01” | 13 | verified | [32] | “2026-10-01” | [] |
| “Verified, SW 2026” | 13 | verified | [34] | *(none)* | [] |
| “Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), configurations probe 2026-11-14” | 13 | verified | [32, 34] | “configurations probe 2026-11-14” | [] |
| “Verified, SW 2024 SP5 (32.5.0), 2026-11-15” | 8 | verified | [32] | “2026-11-15” | [] |
| “Verified, SW 2026 (34.0.0), helical runs 2026-09-15” | 8 | verified | [34] | “helical runs 2026-09-15” | [] |
| “Verified, SW 2024 SP5 (32.5.0), 2026-10-28” | 7 | verified | [32] | “2026-10-28” | [] |
| “Verified, SW 2024 SP5 (32.5.0), 2026-10-06” | 6 | verified | [32] | “2026-10-06” | [] |
| “Verified, SW 2026, Airfoil Converter 2026-09-16” | 5 | verified | [34] | “Airfoil Converter 2026-09-16” | [] |
| “Verified, SW 2026 SP0.0, Airfoil Converter 2026-09-23” | 3 | verified | [34] | “Airfoil Converter 2026-09-23” | [] |
| “Verified not to work, SW 2024 SP5 (32.5.0), 2026-10-30” | 2 | fails | [32] | “2026-10-30” | [] |
| “Verified, SW 2026 (34.0.0), run 20260915-015506” | 2 | verified | [34] | “run 20260915-015506” | [] |
| “Verified, SW 2026 (34.0.0), through `GetDimension2`” | 2 | verified | [34] | “through `GetDimension2`” | [] |
| “Verified, SW 2026 SP0.0, Airfoil Converter 2026-09-27” | 2 | verified | [34] | “Airfoil Converter 2026-09-27” | [] |
| “Observed once (the dialog), SW 2024 SP5 (32.5.0), 2026-11-02; the `0x80010105` verified, tier 7/8 2026-11-13/14” | 1 | fails | [32] | “2026-11-02” | [] |
| “Partly verified” | 1 | partly-verified | [] | *(none)* | [] |
| “Partly verified, SW 2024 SP5 (32.5.0), 2026-10-06” | 1 | partly-verified | [32] | “2026-10-06” | [] |
| “Partly verified, SW 2026 (34.0.0)” | 1 | partly-verified | [34] | *(none)* | [] |
| “Partly verified, SW 2026 SP0.0, Airfoil Converter 2026-09-22” | 1 | partly-verified | [34] | “Airfoil Converter 2026-09-22” | [] |
| “Partly verified, SW 2026, Airfoil Converter 2026-09-16” | 1 | partly-verified | [34] | “Airfoil Converter 2026-09-16” | [] |
| “Put verified, SW 2026 (34.0.0), dev runs 2026-09-15” | 1 | verified | [34] | “dev runs 2026-09-15” | [] |
| “Ran, SW 2024 (32.5.0), 2026-10-01” | 1 | partly-verified | [32] | “2026-10-01” | [] |
| “Read, SW 2024 (32.5.0), 2026-10-01” | 1 | partly-verified | [32] | “2026-10-01” | [] |
| “Set, SW 2026 SP0.0, Airfoil Converter 2026-09-23” | 1 | partly-verified | [34] | “Airfoil Converter 2026-09-23” | [] |
| “Unverified, Airfoil Converter 2026-09-16” | 1 | unverified | [] | “Airfoil Converter 2026-09-16” | [] |
| “Verified absent, SW 2026 (34.1.1), 2026-11-14” | 1 | absent | [34] | “2026-11-14” | [] |
| “Verified absent, Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), tier 7/8 2026-11-13/14” | 1 | absent | [32, 34] | “tier 7/8 2026-11-13/14” | [] |
| “Verified at mark 1, SW 2026 (34.0.0), run 20260915-015506; at mark 256, appended, for a mirror, helical runs 2026-09-15” | 1 | verified | [34] | “run 20260915-015506” | [] |
| “Verified for 1 and 4, verified not to work for 2, SW 2026 SP0.0, Airfoil Converter 2026-09-22” | 1 | partly-verified | [34] | “Airfoil Converter 2026-09-22” | [] |
| “Verified for item 3, SW 2026 SP0.0, Airfoil Converter 2026-09-22” | 1 | partly-verified | [34] | “Airfoil Converter 2026-09-22” | [] |
| “Verified for these values only, SW 2024 SP5 (32.5.0), 2026-10-06” | 1 | verified | [32] | “2026-10-06” | [] |
| “Verified in that one form, SW 2026 SP0.0, Airfoil Converter 2026-09-22” | 1 | verified | [34] | “Airfoil Converter 2026-09-22” | [] |
| “Verified not to carry through gear or lock mates on that train, Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), tier 7/8 2026-11-13/14” | 1 | fails | [32, 34] | “tier 7/8 2026-11-13/14” | [] |
| “Verified not to work from Python this way, SW 2026 SP0.0, Airfoil Converter 2026-09-22” | 1 | fails | [34] | “Airfoil Converter 2026-09-22” | [pywin32] |
| “Verified not to work from Python, SW 2026 SP0.0, Airfoil Converter 2026-09-22” | 1 | fails | [34] | “Airfoil Converter 2026-09-22” | [pywin32] |
| “Verified not to work on STEP, SW 2026 SP1.1” | 1 | fails | [34] | *(none)* | [] |
| “Verified not to work that way, SW 2026 (34.1.1), tier 7/8 2026-11-13/14” | 1 | fails | [34] | “tier 7/8 2026-11-13/14” | [] |
| “Verified not to work there, SW 2026 (34.0.0)” | 1 | fails | [34] | *(none)* | [] |
| “Verified not to work with those arguments, SW 2024 (32.5.0), 2026-10-01” | 1 | fails | [32] | “2026-10-01” | [] |
| “Verified not to work with those two arguments, SW 2026 SP0.0, Airfoil Converter 2026-09-22” | 1 | fails | [34] | “Airfoil Converter 2026-09-22” | [] |
| “Verified not to work, SW 2024 SP5 (32.5.0), 2026-11-09” | 1 | fails | [32] | “2026-11-09” | [] |
| “Verified not to work, SW 2024 SP5 (32.5.0), 2026-11-15” | 1 | fails | [32] | “2026-11-15” | [] |
| “Verified not to work, SW 2026” | 1 | fails | [34] | *(none)* | [] |
| “Verified not to work, SW 2026 (34.0.0)” | 1 | fails | [34] | *(none)* | [] |
| “Verified on a line, SW 2026 (34.0.0)” | 1 | partly-verified | [34] | *(none)* | [] |
| “Verified, SW 2024 SP5 (32.5.0), 2026-10-06 and 2026-10-28” | 1 | verified | [32] | “2026-10-06 and 2026-10-28” | [] |
| “Verified, SW 2024 SP5 (32.5.0), 2026-10-28 (read only)” | 1 | partly-verified | [32] | “2026-10-28” | [] |
| “Verified, SW 2024 SP5 (32.5.0), 2026-10-28 (value suspect)” | 1 | partly-verified | [32] | “2026-10-28” | [] |
| “Verified, SW 2024 SP5 (32.5.0), 2026-11-09; exclusion not reproduced 2026-11-15” | 1 | partly-verified | [32] | “2026-11-09” | [] |
| “Verified, SW 2024/2025/2026” | 1 | verified | [32, 33, 34] | *(none)* | [] |
| “Verified, SW 2025” | 1 | verified | [33] | *(none)* | [] |
| “Verified, SW 2026 (34.0.0), dev runs and helical runs 2026-09-15” | 1 | verified | [34] | “dev runs and helical runs 2026-09-15” | [] |
| “Verified, SW 2026 (34.0.0), rerun 20260914-183429” | 1 | verified | [34] | “rerun 20260914-183429” | [] |
| “Verified, SW 2026 (34.0.0), run 20260915-015506 and helical runs 2026-09-15” | 1 | verified | [34] | “run 20260915-015506 and helical runs 2026-09-15” | [] |
| “Verified, SW 2026 (34.0.0); axes and flip, dev runs 2026-09-15” | 1 | verified | [34] | *(none)* | [] |
| “Verified, SW 2026 (34.0.0); from a line, dev runs 2026-09-15” | 1 | verified | [34] | *(none)* | [] |
| “Verified, SW 2026 (34.0.0); in a 3D sketch SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), 2026-11-14” | 1 | verified | [34] | *(none)* | [] |
| “Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), gear-train runner 2026-11-14” | 1 | verified | [32, 34] | “gear-train runner 2026-11-14” | [] |
| “Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), runs 20261114-133014 and 20261114-135104; follow-up runs 20261114-151013 (2024), 20261114-162034 and 20261114-162546 (2026); whole-application run 2026-11-14 on both, fresh sessions” | 1 | verified | [32, 34] | “runs 20261114-133014 and 20261114-135104” | [] |
| “Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), tier 7/8 2026-11-13/14 (runs 20261114-105135, 20261114-111150)” | 1 | verified | [32, 34] | “tier 7/8 2026-11-13/14 (runs 20261114-105135, 20261114-111150)” | [] |
| “Verified, SW 2026 (34.1.1) only, planetary probe 2026-11-14” | 1 | verified | [34] | “planetary probe 2026-11-14” | [] |
| “Verified, SW 2026 (34.1.1) step by step; SW 2024 SP5 (32.5.0) inside an application build, 2026-11-14” | 1 | verified | [34] | *(none)* | [] |
| “Verified, SW 2026 (34.1.1), probe tier 9 run 20261114-195608; real teeth SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), 2026-11-14” | 1 | verified | [34] | “probe tier 9 run 20261114-195608” | [] |
| “Verified, SW 2026 SP0.0, 14 folder features of a real part, 2026-09-24” | 1 | verified | [34] | “14 folder features of a real part, 2026-09-24” | [] |
| “Verified, SW 2026, Airfoil Converter 2026-09-16 and 2026-09-23” | 1 | verified | [34] | “Airfoil Converter 2026-09-16 and 2026-09-23” | [] |
| “Verified, SW 2026; set, SW 2026 SP0.0 2026-09-23” | 1 | verified | [34] | *(none)* | [] |
| “Verified; `Nothing` on `BlendRefSurface`, SW 2026 SP0.0, Airfoil Converter 2026-09-27” | 1 | verified | [34] | “Airfoil Converter 2026-09-27” | [] |
| “Verified; crash observed, Airfoil Converter 2026-09-16” | 1 | verified | [34] | “Airfoil Converter 2026-09-16” | [] |

## Interface by section

A section's `interface` is the one interface its heading names before any parenthesis;
`null` when it names none or several. A row's bare members take that interface only when
the Member cell names none itself: in a cell such as `ITableAnnotation.RowCount` / `ColumnCount`
the other names stay bare. A dotted path that does not start with an interface
(`Dimension.Name`, `IDimension.Tolerance.Type`) is kept as its last name only. One heading to
look at: 'IBomFeature and the table' gives IBomFeature to its rows that name no interface
(`GetConfigurationCount`, `SetConfigurations`, `FollowAssemblyOrder2`, `TableType`).

| Section (source) | Rows | Interface |
|---|---|---|
| “ISldWorks (the application)” | 32 | ISldWorks |
| “IModelDoc2 (a part, assembly or drawing)” | 51 | IModelDoc2 |
| “IModelDocExtension” | 34 | IModelDocExtension |
| “IConfigurationManager (from `IModelDoc2.ConfigurationManager`)” | 3 | IConfigurationManager |
| “IConfiguration” | 6 | IConfiguration |
| “IPartDoc (a part, cast from IModelDoc2)” | 3 | IPartDoc |
| “IEquationMgr (from `IModelDoc2.GetEquationMgr`)” | 16 | IEquationMgr |
| “IDisplayDimension and IDimension (from a feature)” | 7 | *(null)* |
| “IFeatureManager (from `IModelDoc2.FeatureManager`)” | 25 | IFeatureManager |
| “IFeatureFolder (from `GetSpecificFeature2` on an `FtrFolder`)” | 2 | IFeatureFolder |
| “IFeature” | 32 | IFeature |
| “Curve feature data (from `GetDefinition` on a CurveInFile)” | 2 | *(null)* |
| “Composite curve feature data (from `IFeature.GetDefinition` on a `CompositeCurve`)” | 3 | *(null)* |
| “ISweepFeatureData (from `IFeature.GetDefinition` on a `Sweep` or `SweepCut`)” | 4 | ISweepFeatureData |
| “ISketchManager” | 16 | ISketchManager |
| “ISketch (from `ActiveSketch`, or `GetSpecificFeature2` on a sketch feature)” | 3 | ISketch |
| “ISketchSegment / ISketchPoint” | 10 | *(null)* |
| “ISelectionMgr” | 6 | ISelectionMgr |
| “Geometry interrogation” | 23 | *(null)* |
| “IMassProperty (from `IModelDocExtension.CreateMassProperty`)” | 3 | IMassProperty |
| “IMeasure (from `IModelDocExtension.CreateMeasure`)” | 2 | IMeasure |
| “IMathUtility (from `ISldWorks.GetMathUtility`)” | 1 | IMathUtility |
| “IBody2 (from `IPartDoc.GetBodies2`)” | 7 | IBody2 |
| “IRenderMaterial (from `IModelDocExtension.GetRenderMaterials2`)” | 5 | IRenderMaterial |
| “IModelView (from `IModelDoc2.ActiveView`)” | 1 | IModelView |
| “IDimension / IDisplayDimension” | 5 | *(null)* |
| “IAssemblyDoc (an assembly's document, late-bound)” | 14 | IAssemblyDoc |
| “IComponent2” | 19 | IComponent2 |
| “IDragOperator (from `IAssemblyDoc.GetDragOperator`)” | 6 | IDragOperator |
| “IMate2 (from `IFeature.GetSpecificFeature2` on a mate)” | 6 | IMate2 |
| “IGearMateFeatureData (from `IFeature.GetDefinition` on a `MateGearDim`)” | 9 | IGearMateFeatureData |
| “IDistanceMateFeatureData (from `IFeature.GetDefinition` on a distance mate)” | 3 | IDistanceMateFeatureData |
| “IMateEntity2 (from `IMate2.MateEntity(i)`)” | 3 | IMateEntity2 |
| “IInterferenceDetectionMgr (from `IAssemblyDoc.InterferenceDetectionManager`)” | 6 | IInterferenceDetectionMgr |
| “IDrawingDoc (a drawing, late-bound)” | 13 | IDrawingDoc |
| “ISheet (from `IDrawingDoc.GetCurrentSheet`)” | 3 | ISheet |
| “IView (a drawing view)” | 25 | IView |
| “INote, IAnnotation and ICenterMark (drawing annotations)” | 9 | *(null)* |
| “IDisplayDimension and IDimensionTolerance (on a drawing)” | 12 | *(null)* |
| “IBomFeature and the table (from `IBomTableAnnotation.BomFeature`)” | 12 | IBomFeature |
| “General tables and dimensions added from code” | 6 | *(null)* |
| “Toolbox status and replacing a component” | 2 | *(null)* |
| “ICustomPropertyManager (from `IModelDocExtension.CustomPropertyManager`)” | 1 | ICustomPropertyManager |
| “Explode lines (assembly)” | 2 | *(null)* |
| “Body faces (from `IPartDoc.GetBodies2` and `IBody2.GetFaces`)” | 3 | *(null)* |
| “Constants used” | 0 | *(null)* |

## Rows whose members need a look

| Section | Member cell (source) | Members | Why |
|---|---|---|---|
| IGearMateFeatureData (from `IFeature.GetDefinition` on a `MateGearDim`) | Gear mate with one axis on a turning **carrier** | *(none)* | No backticked name in the cell, so `api_status` cannot reach the row by member; it stays in API-LEDGER.md. |
| IDimension / IDisplayDimension | `Dimension.Name` | Name | A dotted path not of the form Interface.Member: its last name only. |
| IDimension / IDisplayDimension | `Dimension.SystemValue` | SystemValue | A dotted path not of the form Interface.Member: its last name only. |
| IDisplayDimension and IDimensionTolerance (on a drawing) | `IDimension.Tolerance.Type` | Type | A dotted path not of the form Interface.Member: its last name only. |
