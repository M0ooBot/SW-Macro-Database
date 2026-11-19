# Review list: gotchas (step 4)

GOTCHAS.md is now generated from one file per gotcha, `gotchas/NNN-slug.md`, numbers
kept; the generated file was checked equal to the original before it was replaced.
Three things are new and need your eye: the always-list, the bindings a gotcha is
tagged with, and the member tags. Flag only the rows you disagree with.
Written by `tools/migrate.py gotchas` from its ALWAYS, GOTCHA_LANGUAGES and GOTCHA_MEMBERS tables.

## The always-list: please confirm (10)

Rendered into the `sw-macro-database` skill and SW-Agent's own skill, and returned by
`gotchas_for(topic: "always")`. Chosen for silent, destructive or most common failure modes.

| Gotcha | Title | Why always |
|---|---|---|
| [G2](../gotchas/002-the-api-is-in-metres-always.md) | The API is in metres, always | Most common and silent: every length is metres and every angle radians, whatever the document says. |
| [G8](../gotchas/008-solidworks-quietly-renames-on-collision.md) | SolidWorks quietly renames on collision | Silent: a name set on collision becomes another name, and records point at nothing. |
| [G22](../gotchas/022-opening-an-older-file-in-a-newer-solidworks.md) | Opening an older file in a newer SolidWorks makes closing it dangerous | Destructive: closing an upgraded older file can rewrite it in the new format, behind a misleading prompt. |
| [G25](../gotchas/025-the-default-template-can-be-another-year-s-and.md) | The default template can be another year's, and in inches | Silent: a new part can come out in inches from another year's template, and equations follow the units. |
| [G26](../gotchas/026-the-equation-manager-says-no-with-1-not-an.md) | The Equation Manager says no with -1, not an exception | Silent: Equation Manager calls fail by returning -1, never by raising. |
| [G34](../gotchas/034-saveas3-overwrites-an-existing-file-without-a.md) | `SaveAs3` overwrites an existing file without a word | Destructive: SaveAs3 overwrites an existing file and reports success. |
| [G62](../gotchas/062-suppressing-one-feature-suppresses-what-is-built.md) | Suppressing one feature suppresses what is built on it, and unsuppressing does not undo it | Destructive and silent: suppression cascades, and unsuppressing does not bring the rest back. |
| [G93](../gotchas/093-forcerebuild3-false-on-an-assembly-marks-every.md) | `ForceRebuild3(False)` on an assembly marks every component modified | Common and costly: a full assembly rebuild marks every component modified, which turns closes into save prompts. |
| [G100](../gotchas/100-closing-an-assembly-can-raise-a-modal-dialog.md) | Closing an assembly can raise a modal dialog that hangs the script | Hangs: closing an assembly can raise a modal dialog (CAM add-in, older files) that blocks the script. |
| [G108](../gotchas/108-component-handles-go-stale-after-every.md) | Component handles go stale after every `AddConfiguration2` and `ShowConfiguration2`, silently | Silent: every component handle goes stale after a configuration add or show, and answers wrongly instead of failing. |

Considered and not proposed:

| Gotcha | Title | Why not |
|---|---|---|
| [G9](../gotchas/009-rebuilding-per-change-is-both-slow-and-wrong.md) | Rebuilding per change is both slow and wrong | Rebuild once at the end: important, but about speed and transient errors, not silent damage. |
| [G10](../gotchas/010-a-transform-s-rotation-is-stored-by-columns.md) | A transform's rotation is stored by columns | Transform rotation by columns: silent, but only for code that reads transform arrays. |
| [G23](../gotchas/023-showconfiguration2-returns-false-when-the.md) | `ShowConfiguration2` returns False when the configuration is already active | ShowConfiguration2 returning False: a false failure, not damage; G108 covers the dangerous part of configuration work. |
| [G51](../gotchas/051-clearing-the-selection-during-a-user-s-pick.md) | Clearing the selection during a user's pick crashed SolidWorks | Clearing the selection during a user's pick crashed SolidWorks: severe, but only for code that polls the selection while the user works. |
| [G58](../gotchas/058-editrebuild3-returns-false-whenever-anything-in.md) | `EditRebuild3` returns False whenever anything in the part is in error | EditRebuild3 returning False on any error: a misread that stops code, not silent damage. |
| [G95](../gotchas/095-an-over-defining-mate-is-still-made-and-the.md) | An over-defining mate is still made, and the rebuild still says True | An over-defining mate is made anyway: silent, but specific to mate code. |

## Bindings other than `all` (11)

`languages` says how the API must be bound for the gotcha to bite: `all`, `csharp`, `pywin32`
or `late-bound`. Every gotcha not listed here is `[all]`: when the text does not limit it, it
is shown to everyone. SW-Agent's `gotchas_for` filters on this (C# by default).

| Gotcha | Title | Chosen | Why |
|---|---|---|---|
| [G4](../gotchas/004-a-bare-none-is-a-type-mismatch-for-an-absent-com.md) | A bare `None` is a type mismatch for an absent COM object | [pywin32] | Python: "In Python, passing None fails"; the fix is a pywin32 VARIANT. |
| [G5](../gotchas/005-in-late-bound-com-a-zero-argument-method-is-a.md) | In late-bound COM, a zero-argument method is a property get | [pywin32, late-bound] | Titled late-bound COM; observed through pywin32's dynamic dispatch. Early-bound C# calls methods as methods. |
| [G6](../gotchas/006-the-running-object-table-hands-back-an-iunknown.md) | The Running Object Table hands back an `IUnknown` | [pywin32, late-bound] | Late binding needs IDispatch; the code is pywin32. |
| [G7](../gotchas/007-marshal-getactiveobject-does-not-exist-on-modern.md) | `Marshal.GetActiveObject` does not exist on modern .NET | [csharp] | .NET only: Marshal.GetActiveObject is gone on modern .NET. |
| [G21](../gotchas/021-a-late-bound-host-cannot-call-an-api-with-a.md) | A late-bound host cannot call an API with a `ByRef Long` out-parameter | [late-bound, pywin32] | VBScript and PowerShell (late-bound) fail; Python needs a typed VARIANT; VBA and early-bound C# work. |
| [G31](../gotchas/031-a-zero-argument-method-that-returns-nothing-is.md) | A zero-argument method that returns nothing is not called by `call` | [pywin32] | pywin32 attribute access (the "call" helper); "That pywin32 exposes…". |
| [G39](../gotchas/039-imathutility-createtransform-is-member-not-found.md) | `IMathUtility.CreateTransform` is "Member not found" to late binding | [pywin32, late-bound] | Titled late binding; observed through pywin32's dynamic dispatch. |
| [G40](../gotchas/040-interference-detection-three-get-members-are.md) | Interference detection: three `Get` members are properties, `Done` is a method | [pywin32, late-bound] | "through late binding", Python method objects. |
| [G55](../gotchas/055-a-zero-argument-member-that-returns-nothing-or.md) | A zero-argument member that returns nothing *or an array* comes back uncalled | [pywin32] | "a pywin32 late-binding point rather than a SolidWorks one". |
| [G74](../gotchas/074-swcom-connect-refuses-solidworks-2024-and-2025.md) | `swcom.connect()` refuses SolidWorks 2024 and 2025 | [pywin32] | About swcom.py, this repo's Python attach module. |
| [G89](../gotchas/089-silhouette-edges-are-unusable-through-late.md) | Silhouette edges are unusable through late binding | [pywin32, late-bound] | Titled late binding; observed through pywin32. |

## Member tags (116; 49 differ from the proposal)

Proposed: every backticked API name in the gotcha (a name the ledger or an entry's `api`
knows, or one written `Interface.Member`), qualified where the gotcha writes the interface.
Chosen: the proposal less the names the gotcha only mentions in passing (the check it
recommends, the fix, a contrast), so `gotchas_for` on a common member does not return every
gotcha that happens to name it. When in doubt a tag was kept: a missing tag hides a warning.

| Gotcha | Proposed (from the text) | Chosen | Why |
|---|---|---|---|
| [G1](../gotchas/001-the-unversioned-progid-can-point-at-the-wrong.md) | GetObject, GetActiveObject | same |  |
| [G2](../gotchas/002-the-api-is-in-metres-always.md) | *(none)* | same |  |
| [G3](../gotchas/003-insertcurvefile-is-on-the-document-not-the.md) | InsertCurveFile | same |  |
| [G4](../gotchas/004-a-bare-none-is-a-type-mismatch-for-an-absent-com.md) | ModifyDefinition, GetObjectByPersistReference3 | same |  |
| [G5](../gotchas/005-in-late-bound-com-a-zero-argument-method-is-a.md) | RevisionNumber, ActiveDoc, IAssemblyDoc.FixComponent, IBody2.GetEdges, IFace2.GetTessTriangles | same |  |
| [G6](../gotchas/006-the-running-object-table-hands-back-an-iunknown.md) | *(none)* | same |  |
| [G7](../gotchas/007-marshal-getactiveobject-does-not-exist-on-modern.md) | GetActiveObject, GetRunningObjectTable, CreateBindCtx | **GetActiveObject** | GetRunningObjectTable and CreateBindCtx are the way round it, not the trap. |
| [G8](../gotchas/008-solidworks-quietly-renames-on-collision.md) | Name | same |  |
| [G9](../gotchas/009-rebuilding-per-change-is-both-slow-and-wrong.md) | *(none)* | same |  |
| [G10](../gotchas/010-a-transform-s-rotation-is-stored-by-columns.md) | IMathTransform.ArrayData | same |  |
| [G11](../gotchas/011-insertcurvefile-tells-you-true-or-false-and.md) | InsertCurveFile | same |  |
| [G12](../gotchas/012-composite-curve-reads-its-inputs-from-selection.md) | InsertCompositeCurve | same |  |
| [G13](../gotchas/013-a-point-streamed-curve-has-no-file-association.md) | InsertCurveFileBegin, LoadPointsFromFile | same |  |
| [G14](../gotchas/014-inserting-a-curve-does-not-add-it-to-your.md) | InsertCurveFile | same |  |
| [G15](../gotchas/015-never-text-merge-solidworks-binaries.md) | *(none)* | same |  |
| [G16](../gotchas/016-replacereferenceddocument-needs-the-referencing.md) | ReplaceReferencedDocument, GetOpenDocumentByName | **ReplaceReferencedDocument** | GetOpenDocumentByName is the check it recommends, not the trap. |
| [G17](../gotchas/017-check-ignore-and-other-verifications-that-read.md) | *(none)* | same |  |
| [G18](../gotchas/018-movetofolder-does-not-move-anything.md) | IFeatureManager.MoveToFolder, InsertFeatureTreeFolder2 | same |  |
| [G19](../gotchas/019-a-folder-is-two-features-in-the-tree.md) | FirstFeature, GetNextFeature, IFeatureFolder.GetFeatures, GetFirstSubFeature | same |  |
| [G20](../gotchas/020-opendoc6-cannot-open-a-step-file-that-loadfile4.md) | ISldWorks.OpenDoc6, ISldWorks.LoadFile4, GetOpenDocSpec | **ISldWorks.OpenDoc6, ISldWorks.LoadFile4, OpenDoc7, GetOpenDocSpec** | OpenDoc7 added: the text names it as no way out for STEP (it was not in the ledger, so the proposal missed it). |
| [G21](../gotchas/021-a-late-bound-host-cannot-call-an-api-with-a.md) | OpenDoc6, LoadFile4 | same |  |
| [G22](../gotchas/022-opening-an-older-file-in-a-newer-solidworks.md) | ISldWorks.CloseDoc, QuitDoc | **ISldWorks.CloseDoc, QuitDoc, CloseAllDocuments** | CloseAllDocuments added: the text names it as raising the prompt (not in the ledger, so the proposal missed it). |
| [G23](../gotchas/023-showconfiguration2-returns-false-when-the.md) | ShowConfiguration2, GetSaveFlag, DeleteConfiguration2, DeleteDesignTable, GetConfigurationNames | **ShowConfiguration2, DeleteConfiguration2, DeleteDesignTable, GetConfigurationNames** | GetSaveFlag is how the side effect was observed, in passing. |
| [G24](../gotchas/024-getpartbox-is-the-exception-to-2.md) | IPartDoc.GetPartBox | same |  |
| [G25](../gotchas/025-the-default-template-can-be-another-year-s-and.md) | ISldWorks.GetDocumentTemplate, IModelDocExtension.SetUserPreferenceInteger | **ISldWorks.GetDocumentTemplate** | SetUserPreferenceInteger is the fix (set the units), not the trap. |
| [G26](../gotchas/026-the-equation-manager-says-no-with-1-not-an.md) | IEquationMgr.Add3, Add2, IEquationMgr.SetEquationAndConfigurationOption, Equation, Invoke, Status | **IEquationMgr.Add3, Add2, IEquationMgr.SetEquationAndConfigurationOption** | Equation(i) is the working alternative; Invoke is pywin32, not the API; Status is how -1 was read. |
| [G27](../gotchas/027-sqr-0-is-refused-and-iif-does-not-guard-it.md) | *(none)* | same |  |
| [G28](../gotchas/028-an-unbracketed-comparison-binds-before-the.md) | *(none)* | same |  |
| [G29](../gotchas/029-an-equation-driven-curve-s-trig-is-radians-and-a.md) | ISketchManager.CreateEquationSpline2 | same |  |
| [G30](../gotchas/030-sgequal-did-nothing-to-two-circles.md) | *(none)* | **sgEQUAL** | sgEQUAL added: the backticked relation constant the gotcha is about (a constant, so not in the proposal). |
| [G31](../gotchas/031-a-zero-argument-method-that-returns-nothing-is.md) | IAssemblyDoc.FixComponent, IsFixed | **IAssemblyDoc.FixComponent** | IsFixed is how the effect was checked, in passing. |
| [G32](../gotchas/032-a-through-all-cut-in-the-default-direction-made.md) | IFeatureManager.FeatureCut4 | same |  |
| [G33](../gotchas/033-find-a-feature-s-dimension-by-its-value-not-by.md) | *(none)* | same |  |
| [G34](../gotchas/034-saveas3-overwrites-an-existing-file-without-a.md) | IModelDocExtension.SaveAs3, IModelDoc2.SaveAs3 | same |  |
| [G35](../gotchas/035-an-entity-drawn-starting-on-another-s-end-shares.md) | GetStartPoint2, GetSelectedObjectCount2 | same |  |
| [G36](../gotchas/036-a-new-sketch-point-once-could-not-be-selected.md) | ISketchPoint.Select4, ISelectionMgr.GetSelectedObjectCount2, IModelDocExtension.SelectByID2 | **ISketchPoint.Select4** | An observation, not a rule: SelectByID2 and GetSelectedObjectCount2 are the fallback and the check, and tagging them would show a one-off on every selection. |
| [G37](../gotchas/037-from-a-sub-feature-getnextfeature-walks-on.md) | GetNextFeature, IFeature.GetFirstSubFeature, IFeature.GetNextSubFeature | same |  |
| [G38](../gotchas/038-with-two-centrelines-in-a-sketch-the-revolve.md) | IFeatureManager.FeatureRevolve2, SelectByID2 | **IFeatureManager.FeatureRevolve2** | SelectByID2 is how the axis was selected (mark 16), in passing. |
| [G39](../gotchas/039-imathutility-createtransform-is-member-not-found.md) | IMathUtility.CreateTransform, DISPATCH_METHOD, IComponent2.Transform2 | **IMathUtility.CreateTransform** | DISPATCH_METHOD is pywin32, not the API; IComponent2.Transform2 is where the result goes, in passing. |
| [G40](../gotchas/040-interference-detection-three-get-members-are.md) | Done, GetInterferenceCount, GetInterferences, IInterference.Volume | same |  |
| [G41](../gotchas/041-addcomponent5-does-not-put-the-part-s-origin-at.md) | AddComponent5, Transform2 | **AddComponent5** | Transform2 is the fix (set every frame), not the trap. |
| [G42](../gotchas/042-a-point-to-plane-distance-mate-is-measured-along.md) | AddMate5 | same |  |
| [G43](../gotchas/043-an-angle-dimension-on-the-top-plane-give-its.md) | IModelDoc2.AddDimension2 | same |  |
| [G44](../gotchas/044-a-move-copy-body-turn-records-no-dimension-so-no.md) | IFeatureManager.InsertMoveCopyBody2, IBody2.Select2 | **IFeatureManager.InsertMoveCopyBody2** | IBody2.Select2 is how the body was selected, in passing. |
| [G45](../gotchas/045-a-sweep-s-twist-sign-is-ignored-the-other-hand.md) | D1ReverseTwistDir, IFeatureManager.InsertProtrusionSwept4, IFeature.GetDefinition, ISweepFeatureData.AccessSelections, IFeature.ModifyDefinition, InsertCutSwept5 | **D1ReverseTwistDir, IFeatureManager.InsertProtrusionSwept4, InsertCutSwept5** | GetDefinition, AccessSelections and ModifyDefinition are the ordinary route to the flag, not the trap. |
| [G46](../gotchas/046-arctan-is-refused-the-inverse-tangent-is-atn.md) | IEquationMgr.Add2 | same |  |
| [G47](../gotchas/047-mirroring-a-body-the-body-goes-at-mark-256-and-a.md) | IFeatureManager.InsertMirrorFeature2, IBody2.Select2, ISelectionMgr.CreateSelectData | same |  |
| [G48](../gotchas/048-twisted-and-patterned-spline-cuts-weigh-close-to.md) | *(none)* | same |  |
| [G49](../gotchas/049-deleting-a-composite-curve-deletes-the-loft.md) | *(none)* | same |  |
| [G50](../gotchas/050-the-order-guides-are-picked-in-can-change-the.md) | *(none)* | same |  |
| [G51](../gotchas/051-clearing-the-selection-during-a-user-s-pick.md) | IModelDoc2.ClearSelection2, ISketchManager.ActiveSketch | **IModelDoc2.ClearSelection2** | ISketchManager.ActiveSketch is the guard it recommends, not the trap. |
| [G52](../gotchas/052-guides-too-close-to-a-sharp-corner-break-a-loft.md) | *(none)* | same |  |
| [G53](../gotchas/053-a-curve-file-with-near-duplicate-points-is.md) | *(none)* | same |  |
| [G54](../gotchas/054-walking-the-feature-tree-every-second-makes.md) | FirstFeature, GetNextFeature, IModelDoc2.GetFeatureCount, GetUpdateStamp | **FirstFeature, GetNextFeature** | GetFeatureCount and GetUpdateStamp are the cheap alternative, not the trap. |
| [G55](../gotchas/055-a-zero-argument-member-that-returns-nothing-or.md) | ReleaseSelectionAccess, IBody2.GetEdges, IFace2.GetTessTriangles, IAssemblyDoc.FixComponent, GetFaces, GetBody, GetCurve, GetMassProperties, IsRolledBack, Name, GetTypeName2, GetNextFeature, InsertPlanarRefSurface, IMassProperty.AddBodies, IModelDocExtension.DeleteDisplayStateSpecificRenderMaterial, DISPATCH_METHOD, IModelDocExtension.CreateBalloonOptions, IEdge.GetCurveParams2, IModelDoc2.EditRebuild3, INote.GetBalloonStyle, IMeasure.Calculate, ISldWorks.ExitApp | **ReleaseSelectionAccess, IBody2.GetEdges, IFace2.GetTessTriangles, IAssemblyDoc.FixComponent, IMassProperty.AddBodies, IModelDocExtension.DeleteDisplayStateSpecificRenderMaterial, IModelDocExtension.CreateBalloonOptions, IEdge.GetCurveParams2, IModelDoc2.EditRebuild3, INote.GetBalloonStyle, IMeasure.Calculate, ISldWorks.ExitApp** | Dropped the members it lists as observed not to need this (GetFaces, GetBody, GetCurve, GetCurveParams2 on 2026, GetMassProperties, IsRolledBack, Name, GetTypeName2, GetNextFeature, InsertPlanarRefSurface) and DISPATCH_METHOD (pywin32). |
| [G56](../gotchas/056-reloading-a-curve-is-charged-for-the-whole-tree.md) | IFeature.ModifyDefinition, LoadPointsFromFile, ISldWorks.CommandInProgress, IFeatureManager.EditRollback | same |  |
| [G57](../gotchas/057-editrollback-to-the-previous-position-answers.md) | IFeatureManager.EditRollback, IModelDoc2.FeatureByPositionReverse, IsRolledBack, IFeatureManager.GetRollbackBarPosition | **IFeatureManager.EditRollback, IFeatureManager.GetRollbackBarPosition** | FeatureByPositionReverse and IsRolledBack are the check it recommends. |
| [G58](../gotchas/058-editrebuild3-returns-false-whenever-anything-in.md) | EditRebuild3, ForceRebuild3 | same |  |
| [G59](../gotchas/059-accessselections-rolls-the-tree-back-and-the.md) | AccessSelections, ReleaseSelectionAccess | same |  |
| [G60](../gotchas/060-a-planar-cap-can-span-a-sliver-instead-of-the.md) | IModelDoc2.InsertPlanarRefSurface, IFace2.GetArea | **IModelDoc2.InsertPlanarRefSurface** | IFace2.GetArea is the check it recommends. |
| [G61](../gotchas/061-a-knit-asked-for-a-solid-can-sew-a-sheet-and.md) | IFeatureManager.InsertSewRefSurface, GetMassProperties, IPartDoc.GetBodies2 | **IFeatureManager.InsertSewRefSurface** | GetMassProperties and GetBodies2 are how it was detected. |
| [G62](../gotchas/062-suppressing-one-feature-suppresses-what-is-built.md) | IFeature.SetSuppression2, IsSuppressed | **IFeature.SetSuppression2** | IsSuppressed is the snapshot it recommends. |
| [G63](../gotchas/063-a-six-decimal-curve-file-can-make-a-flat-loft.md) | InsertProtrusionBlend2 | same |  |
| [G64](../gotchas/064-guides-that-land-on-each-section-s-nearest-point.md) | *(none)* | same |  |
| [G65](../gotchas/065-a-round-nose-cut-into-two-curves-comes-out-a.md) | *(none)* | same |  |
| [G66](../gotchas/066-diffing-the-tree-around-every-insert-costs-two.md) | InsertCurveFile, IModelDoc2.GetFeatureCount, IModelDocExtension.GetLastFeatureAdded, IPartDoc.FeatureByName | **InsertCurveFile, IModelDocExtension.GetLastFeatureAdded** | GetFeatureCount and FeatureByName are named only as quick alternatives. |
| [G67](../gotchas/067-deleting-a-surface-loft-deletes-the-caps-built.md) | *(none)* | same |  |
| [G68](../gotchas/068-a-surface-loft-has-no-feature-data.md) | IFeature.GetDefinition | same |  |
| [G69](../gotchas/069-the-journal-records-a-program-s-calls-but-not.md) | IFeature.Select2, IFeature.Name, IModelDocExtension.SaveAs, Save3 | **(none)** | About the journal: Select2, Name, SaveAs and Save3 are examples of what it records, and tagging them would show this on every rename and save. |
| [G70](../gotchas/070-deletedisplaystatespecificrendermaterial-wants.md) | IModelDocExtension.DeleteDisplayStateSpecificRenderMaterial, IRenderMaterial.GetMaterialIds | same |  |
| [G71](../gotchas/071-zeroing-an-appearance-s-transparency-does-not.md) | GetRenderMaterialsCount2 | same |  |
| [G72](../gotchas/072-hh-exe-decompile-made-nothing-from-the-chm-s.md) | *(none)* | same |  |
| [G73](../gotchas/073-placing-a-component-and-rebuilding-ignores-gear.md) | Transform2, EditRebuild3, GetErrorCode2 | **Transform2, EditRebuild3** | GetErrorCode2 is how errors were read, in passing. |
| [G74](../gotchas/074-swcom-connect-refuses-solidworks-2024-and-2025.md) | *(none)* | same |  |
| [G75](../gotchas/075-a-gear-mate-s-numerator-belongs-to-its-second.md) | GearRatioNumerator, IMate2.MateEntity, EntityParams | same |  |
| [G76](../gotchas/076-mate-folders-do-not-contain-their-mates.md) | GetFirstSubFeature, GetNextSubFeature, IMate2.Type | same |  |
| [G77](../gotchas/077-a-drawing-s-first-model-view-rescales-the-sheet.md) | IDrawingDoc.CreateDrawViewFromModelView3, IView.UseSheetScale, ISheet.SetScale, ScaleDecimal | **IDrawingDoc.CreateDrawViewFromModelView3, ISheet.SetScale** | UseSheetScale and ScaleDecimal are the fix and the check. |
| [G78](../gotchas/078-a-bom-inserted-from-code-lists-nothing-until-its.md) | IView.InsertBomTable5, IBomFeature.GetConfigurationCount, SetConfigurations | **IView.InsertBomTable5, SetConfigurations** | GetConfigurationCount is how the cause was read. |
| [G79](../gotchas/079-insertnote-puts-the-note-in-the-active-view.md) | IModelDoc2.InsertNote, IDrawingDoc.EditSheet, ClearSelection2 | **IModelDoc2.InsertNote** | EditSheet and ClearSelection2 are the fix. |
| [G80](../gotchas/080-iannotation-select3-then-editdelete-deleted.md) | IAnnotation.Select3, EditDelete, GetAnnotation, IModelDocExtension.SelectByID2, ICenterMark.Select | **IAnnotation.Select3, EditDelete** | GetAnnotation is how it was reached; SelectByID2 is the fix; ICenterMark.Select is a contrast. |
| [G81](../gotchas/081-auto-balloon-skips-parts-it-cannot-see-without.md) | IDrawingDoc.AutoBalloon5 | same |  |
| [G82](../gotchas/082-a-drawing-view-can-name-a-configuration-and-draw.md) | ReferencedConfiguration, ForceRebuild3, ShowConfiguration2 | **ReferencedConfiguration** | ForceRebuild3 and ShowConfiguration2 are the fix. |
| [G83](../gotchas/083-component-positions-are-not-stored-per.md) | AddMate5, Transform2, ForceRebuild3 | **AddMate5, Transform2** | ForceRebuild3 is how a later measurement rebuilt, in passing. |
| [G84](../gotchas/084-deleted-smart-explode-line-segments-come-back.md) | EditDelete, InsertExplodeLineSketch | same |  |
| [G85](../gotchas/085-explode-lines-are-hidden-in-a-drawing-view-that.md) | SelectByID2, UnblankSketch | **UnblankSketch** | SelectByID2 is how the sketch was selected, in passing. |
| [G86](../gotchas/086-a-drawing-view-s-position-is-its-outline-s.md) | IView.Position, ArrayData | **IView.Position** | ArrayData is the fix (read the model origin), in passing. |
| [G87](../gotchas/087-a-line-sketched-in-a-drawing-view-uses-the-view.md) | ISketchManager.CreateLine, IView.GetXform, IView.Angle | **ISketchManager.CreateLine** | IView.GetXform and IView.Angle are the conversion it recommends. |
| [G88](../gotchas/088-a-section-view-can-come-out-upside-down-and-a.md) | CreateSectionViewAt5, IView.Angle | **CreateSectionViewAt5** | IView.Angle is the fix. |
| [G89](../gotchas/089-silhouette-edges-are-unusable-through-late.md) | IView.GetVisibleEntities2, GetCurve, Select2 | same |  |
| [G90](../gotchas/090-a-toolbox-flagged-component-reloads-from-the.md) | ReplaceComponents2 | same |  |
| [G91](../gotchas/091-editing-a-bom-cell-writes-to-the-part-s-property.md) | Text, Description, InsertColumn2 | **Text** | Description is a custom property name, not a member; InsertColumn2 is the alternative. |
| [G92](../gotchas/092-auto-balloons-can-show-each-part-s-quantity-with.md) | AutoBalloon5, InsertBOMBalloon2, IBalloonOptions.ShowQuantity, CreateBalloonOptions | **AutoBalloon5, CreateBalloonOptions** | InsertBOMBalloon2 and IBalloonOptions.ShowQuantity are the alternative that works. |
| [G93](../gotchas/093-forcerebuild3-false-on-an-assembly-marks-every.md) | ForceRebuild3, GetSaveFlag, EditRebuild3, Transform2 | **ForceRebuild3** | EditRebuild3 and Transform2 are the contrast (they did not mark everything); GetSaveFlag is how it was read. |
| [G94](../gotchas/094-two-reference-axes-cannot-be-mated-concentric.md) | AddMate5 | same |  |
| [G95](../gotchas/095-an-over-defining-mate-is-still-made-and-the.md) | AddMate5, ForceRebuild3, GetErrorCode2, GetConstrainedStatus, GetWhatsWrongCount | **AddMate5, ForceRebuild3, GetErrorCode2** | GetConstrainedStatus and GetWhatsWrongCount are the checks it recommends. |
| [G96](../gotchas/096-a-gear-mate-s-ratio-goes-in-first-selection.md) | AddMate5, GearRatioNumerator, MateEntity | same |  |
| [G97](../gotchas/097-on-solidworks-2024-a-gear-mate-changed-by.md) | IFeature.ModifyDefinition, CloseDoc | same |  |
| [G98](../gotchas/098-a-put-on-a-locked-or-gear-mated-gear-moves-that.md) | Transform2, SetTransformAndSolve2, Drag, DragAsUI | same |  |
| [G99](../gotchas/099-addcomponent5-of-a-part-that-is-not-open-returns.md) | AddComponent5, OpenDoc6 | same |  |
| [G100](../gotchas/100-closing-an-assembly-can-raise-a-modal-dialog.md) | CloseDoc, QuitDoc, GetSaveFlag | **CloseDoc, QuitDoc** | GetSaveFlag is how the state was read, in passing. |
| [G101](../gotchas/101-the-drag-operator-did-not-turn-a-gear-train-held.md) | AddComponent, TransformType, UseAbsoluteTransform, DragMode, Drag, EndDrag | **Drag** | AddComponent, TransformType, UseAbsoluteTransform, DragMode and EndDrag are the recipe repeated, not the trap; a bare AddComponent would also match IAssemblyDoc.AddComponent. |
| [G102](../gotchas/102-forcing-lightweight-needs-two-flags-and-the-cam.md) | OpenDoc6, GetSuppression2 | **OpenDoc6** | GetSuppression2 is the check it recommends. |
| [G103](../gotchas/103-a-suppressed-mate-reads-error-code-0-and.md) | GetErrorCode2, SetSuppression2, GetSaveFlag | **GetErrorCode2, SetSuppression2** | GetSaveFlag is how the side effect was read. |
| [G104](../gotchas/104-no-interference-after-a-gear-change-proves.md) | *(none)* | same |  |
| [G105](../gotchas/105-the-flip-a-toothed-ring-gear-s-gear-mate-needs.md) | AddMate5, CommandInProgress, IGearMateFeatureData.Reverse, IMateEntity2.EntityParams | **AddMate5, IGearMateFeatureData.Reverse, IMateEntity2.EntityParams** | CommandInProgress is one condition tried, in passing. |
| [G106](../gotchas/106-a-gear-mate-between-non-parallel-axes-the-flip.md) | AddMate5, IMateEntity2.EntityParams, IGearMateFeatureData.Reverse | same |  |
| [G107](../gotchas/107-a-gear-mate-holds-its-ratio-relative-to-the-line.md) | *(none)* | same |  |
| [G108](../gotchas/108-component-handles-go-stale-after-every.md) | AddConfiguration2, ShowConfiguration2, Transform2, IsFixed, IAssemblyDoc.GetComponentByName, DeleteConfiguration2 | **AddConfiguration2, ShowConfiguration2, Transform2, IsFixed** | GetComponentByName is the fix; DeleteConfiguration2 is the contrast (handles stayed good). |
| [G109](../gotchas/109-setsuppression2-per-configuration-straight-after.md) | AddConfiguration2, IFeature.SetSuppression2, IsSuppressed2 | **IFeature.SetSuppression2, AddConfiguration2** | IsSuppressed2 is the check it recommends. |
| [G110](../gotchas/110-a-dimension-s-value-per-configuration.md) | GetSystemValue3, IDimension.SetSystemValue3, IDimension.SystemValue, IEquationMgr.Add2 | same |  |
| [G111](../gotchas/111-a-section-view-s-excluded-components-can-be.md) | CreateSectionViewAt5, IView.GetSection, SetExcludedComponents, Invoke | **CreateSectionViewAt5, IView.GetSection, SetExcludedComponents** | Invoke is pywin32, not the API. |
| [G112](../gotchas/112-section-hatching-is-missing-until-the-drawing-is.md) | ForceRebuild3, SaveAs, EditRebuild3 | **ForceRebuild3, EditRebuild3** | SaveAs is the export that showed it, in passing. |
| [G113](../gotchas/113-mate-entities-read-before-a-configuration-switch.md) | ShowConfiguration2, AddMate5 | same |  |
| [G114](../gotchas/114-showconfiguration2-can-raise-and-still-switch.md) | ShowConfiguration2, ForceRebuild3, Name, SetSuppression2 | **ShowConfiguration2, ForceRebuild3** | Name is the check; SetSuppression2 is a cross-reference. |
| [G115](../gotchas/115-in-context-geometry-is-per-part-configuration.md) | ReferencedConfiguration | same |  |
| [G116](../gotchas/116-equation-calls-refuse-a-virtual-in-context-part.md) | Delete, Add2, Add3, SetEquationAndConfigurationOption | same |  |
