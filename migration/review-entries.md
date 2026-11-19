# Review list: entries (step 3)

Every entry keeps its one `status` and its `verified_on` text, copied as written.
`majors` is new: the revision majors (32 = SolidWorks 2024, 33 = 2025, 34 = 2026) that
`verified_on` names, taken from its main clause only, with the most conservative
value the text supports. Read the rows and flag only those you disagree with.
Written by `tools/migrate.py entries`; the choices are its NO_RUN and MAJORS_OVERRIDE tables.

## Status changes proposed (2)

| Entry | Source text (`verified_on`) | Was | Proposed | Majors | Why |
|---|---|---|---|---|---|
| [connect-04-attach-vba](../entries/connect/04-attach-from-vba.md) | “standard across versions” | verified | **unverified** | [] | Records no run: "standard across versions" is a claim about the API, not an observation. Proposed unverified (the flag can choose partly-verified; verified needs an observation). The body's **Status:** line still says Verified: bodies are not edited here, so if the downgrade stands, a follow-up should change that line too. |
| [sketches-06-sketch-api-limits](../entries/sketches/06-what-the-sketch-api-cannot-do.md) | “documented API surface as of SW 2026” | verified | **unverified** | [] | Records no run: "documented API surface" is the help's word, not an observation. Proposed unverified (the flag can choose partly-verified). The body's **Status:** line still says Verified: bodies are not edited here, so if the downgrade stands, a follow-up should change that line too. |

## Majors chosen with judgment (24)

The text is partial (a semicolon, "also", "for the …") or names several versions at once.

| Entry | Source text (`verified_on`) | Status | Main clause gives | Chosen | Why |
|---|---|---|---|---|---|
| [assemblies-01-new-assembly-and-insert-components](../entries/assemblies/01-new-assembly-and-insert-components.md) | “SolidWorks 2026 (revision 34.0.0); inserting a closed part, a fixed component's put, and the template's effect on fixing also on 34.1.1 and SolidWorks 2024 SP5 (32.5.0)” | verified | [34] | **[34]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [assemblies-02-mates-from-code](../entries/assemblies/02-mates-from-code.md) | “SolidWorks 2026 (revisions 34.0.0 and 34.1.1); failing mates, deleting and renaming also on SolidWorks 2024 SP5 (32.5.0)” | verified | [34] | **[34]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [assemblies-04-mates-between-non-parallel-axes](../entries/assemblies/04-mates-between-non-parallel-axes.md) | “SolidWorks 2026 (revisions 34.0.0 and 34.1.1); the gear mate sense also on SolidWorks 2024 SP5 (32.5.0), three meshes” | verified | [34] | **[34]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [assemblies-05-test-motion-with-the-drag-operator](../entries/assemblies/05-test-motion-with-the-drag-operator.md) | “SolidWorks 2024 SP5 (32.5.0); the gear-train drags also on SolidWorks 2026 (revisions 34.0.0 and 34.1.1)” | partly-verified | [32] | **[32]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [assemblies-06-read-every-mate](../entries/assemblies/06-read-every-mate.md) | “SolidWorks 2024 SP5 (32.5.0); the MateEntity order of code-made mates and code-made mate folders also SolidWorks 2026 (34.1.1)” | verified | [32] | **[32]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [assemblies-10-mate-a-gear-train-that-turns](../entries/assemblies/10-mate-a-gear-train-that-turns.md) | “SolidWorks 2026 (revisions 34.0.0 and 34.1.1) and SolidWorks 2024 SP5 (32.5.0)” | verified | [32, 34] | **[32, 34]** | The main clause names each of these versions for the whole claim. |
| [assemblies-11-change-a-mated-gear-train](../entries/assemblies/11-change-a-mated-gear-train.md) | “SolidWorks 2026 (revisions 34.0.0 and 34.1.1) and SolidWorks 2024 SP5 (32.5.0), each in a session started fresh for the run” | verified | [32, 34] | **[32, 34]** | The main clause names each of these versions for the whole claim. |
| [assemblies-12-rebuild-scope-and-the-save-flag](../entries/assemblies/12-rebuild-scope-and-the-save-flag.md) | “SolidWorks 2026 (revision 34.1.1) and SolidWorks 2024 SP5 (32.5.0), each in a session started fresh for the run” | verified | [32, 34] | **[32, 34]** | The main clause names each of these versions for the whole claim. |
| [assemblies-13-assembly-configurations-from-code](../entries/assemblies/13-assembly-configurations-from-code.md) | “SolidWorks 2026 (34.1.1) and SolidWorks 2024 SP5 (32.5.0)” | verified | [32, 34] | **[32, 34]** | The main clause names each of these versions for the whole claim. |
| [connect-02-attach-python](../entries/connect/02-attach-from-python.md) | “SolidWorks 2024, 2025 and 2026 side by side” | verified | [32, 33, 34] | **[32, 33, 34]** | The main clause names each of these versions for the whole claim. |
| [connect-03-attach-csharp](../entries/connect/03-attach-from-csharp.md) | “SolidWorks 2026 for attach and dependency read” | partly-verified | [34] | **[34]** | The main clause names this version; the rest qualifies how or what, not where. |
| [connect-05-choosing-among-versions](../entries/connect/05-choosing-among-versions.md) | “a machine carrying SolidWorks 2024, 2025 and 2026” | verified | [32, 33, 34] | **[32, 34]** | The main clause names a machine that carried three versions, not three runs. The body records runs on 2026 (choose()) and on 2024 SP5 (32.5.0: WrongVersion, and a read-only tool through find_candidates()), and says "Not tried: 2025 (major 33)". |
| [connect-09-launch-versus-attach](../entries/connect/09-launch-versus-attach.md) | “SolidWorks 2026 for attach; launch path compiles and runs, ExitApp untested; the hidden-instance warning observed on 2026 SP1.1” | partly-verified | [34] | **[34]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [connect-10-driving-from-outside-windows](../entries/connect/10-driving-from-outside-windows.md) | “WSL2 to SolidWorks 2026” | verified | [34] | **[34]** | The main clause names this version; the rest qualifies how or what, not where. |
| [connect-12-read-the-api-help-offline](../entries/connect/12-read-the-api-help-offline.md) | “SolidWorks 2024 SP5 install, Windows 11, driven from WSL2” | verified | [32] | **[32]** | The main clause names this version; the rest qualifies how or what, not where. |
| [curves-01-sldcrv-format](../entries/curves/01-sldcrv-file-format.md) | “SolidWorks 2025 and 2026” | verified | [33, 34] | **[33, 34]** | The main clause names each of these versions for the whole claim. |
| [documents-02-save-as-and-close](../entries/documents/02-save-as-and-close.md) | “SolidWorks 2026 (revision 34.0.0); closing assemblies also on 34.1.1 and SolidWorks 2024 SP5 (32.5.0)” | verified | [34] | **[34]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [features-12-guided-loft](../entries/features/12-guided-loft.md) | “SolidWorks 2026 for the solid loft and its settings; the surface fallback's arguments were not examined” | partly-verified | [34] | **[34]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [files-01-batch-convert-step](../entries/files/01-batch-convert-step.md) | “SolidWorks 2026 SP1.1 for the C# converter; the VBA macro is the same sequence with a different save call and was not run end to end” | partly-verified | [34] | **[34]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [files-04-export-a-body-to-step](../entries/files/04-export-a-body-to-step.md) | “SolidWorks 2026 for the STEP export and for the suppression and its cascade; that each file of an earlier batch held only its own loft was never checked file by file” | partly-verified | [34] | **[34]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [reading-08-dimensions-and-equations](../entries/reading/08-dimensions-and-equations.md) | “SolidWorks 2026 SP1.1 for the open, configuration and size passes; the dimension and equation walks ran in the same tool but their output was not retained” | partly-verified | [34] | **[34]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [reading-16-measure-between-two-selections](../entries/reading/16-measure-between-two-selections.md) | “SolidWorks 2026 (revision 34.1.1) and SolidWorks 2024 SP5 (32.5.0)” | verified | [32, 34] | **[32, 34]** | The main clause names each of these versions for the whole claim. |
| [sketches-02-3d-sketch-as-vba](../entries/sketches/02-3d-sketch-as-vba.md) | “SolidWorks 2026 (34.1.1), opening and closing a 3D sketch and drawing one line in it from Python, step by step; SolidWorks 2024 SP5 (32.5.0) inside an application build, where only the resulting axis on the line was read; the VBA listings were not run” | partly-verified | [34] | **[34]** | Only the main clause, before the semicolon, counts; what follows covers part of the claim. |
| [sketches-05-units-and-number-format](../entries/sketches/05-units-and-number-format.md) | “SolidWorks 2025 and 2026” | verified | [33, 34] | **[33, 34]** | The main clause names each of these versions for the whole claim. |

## Copied as parsed (72)

One version, stated plainly; the majors are that version. Listed so every entry is here.

| Entry | Source text (`verified_on`) | Status | Majors |
|---|---|---|---|
| [appearance-01-read-and-remove-a-part-appearance](../entries/appearance/01-read-and-remove-a-part-appearance.md) | “SolidWorks 2024 SP5 (revision 32.5.0)” | verified | [32] |
| [assemblies-03-interference-detection](../entries/assemblies/03-interference-detection.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [assemblies-07-configurations-that-hold-different-positions](../entries/assemblies/07-configurations-that-hold-different-positions.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [assemblies-08-exploded-view-from-code](../entries/assemblies/08-exploded-view-from-code.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [assemblies-09-keep-an-edited-toolbox-copy](../entries/assemblies/09-keep-an-edited-toolbox-copy.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [assemblies-14-in-context-part-across-configurations](../entries/assemblies/14-in-context-part-across-configurations.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [connect-01-attach-vbscript](../entries/connect/01-attach-from-vbscript.md) | “SolidWorks 2026” | verified | [34] |
| [connect-06-one-apartment-thread](../entries/connect/06-one-apartment-thread.md) | “SolidWorks 2026” | verified | [34] |
| [connect-07-find-open-document](../entries/connect/07-find-the-open-document.md) | “SolidWorks 2026” | verified | [34] |
| [connect-08-find-feature-by-name](../entries/connect/08-find-a-feature-by-name.md) | “SolidWorks 2026” | verified | [34] |
| [connect-11-probe-an-api-member-on-a-live-session](../entries/connect/11-probe-an-api-member-on-a-live-session.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [curves-02-insert-curve-from-file](../entries/curves/02-insert-curve-from-file.md) | “SolidWorks 2026” | verified | [34] |
| [curves-03-stream-curve-points](../entries/curves/03-stream-curve-points.md) | “SolidWorks 2025” | verified | [33] |
| [curves-04-reload-curve-in-place](../entries/curves/04-reload-curve-in-place.md) | “SolidWorks 2026” | verified | [34] |
| [curves-05-read-curve-points-back](../entries/curves/05-read-curve-points-back.md) | “SolidWorks 2026” | verified | [34] |
| [curves-06-composite-curve](../entries/curves/06-composite-curve.md) | “SolidWorks 2026” | verified | [34] |
| [curves-07-rename-a-feature](../entries/curves/07-rename-a-feature.md) | “SolidWorks 2026” | verified | [34] |
| [curves-08-rebuild-once](../entries/curves/08-rebuild-once-at-the-end.md) | “SolidWorks 2026” | verified | [34] |
| [curves-09-curves-as-loft-profiles](../entries/curves/09-curves-as-loft-profiles.md) | “SolidWorks 2026” | verified | [34] |
| [curves-10-persistent-references](../entries/curves/10-persistent-references.md) | “SolidWorks 2026” | verified | [34] |
| [curves-11-feature-tree-folders](../entries/curves/11-feature-tree-folders.md) | “SolidWorks 2026” | verified | [34] |
| [curves-12-roll-the-tree-back-before-reloading](../entries/curves/12-roll-the-tree-back-before-reloading.md) | “SolidWorks 2026 SP0.0 (revision 34.0.0)” | verified | [34] |
| [documents-01-new-part-from-template](../entries/documents/01-new-part-from-template.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [drawings-01-new-drawing-and-place-views](../entries/drawings/01-new-drawing-and-place-views.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [drawings-02-bom-table-and-balloons](../entries/drawings/02-bom-table-and-balloons.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [drawings-03-notes-title-block-and-deleting-annotations](../entries/drawings/03-notes-title-block-and-deleting-annotations.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [drawings-04-centre-marks-and-centre-lines](../entries/drawings/04-centre-marks-and-centre-lines.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [drawings-05-read-and-tidy-dimensions](../entries/drawings/05-read-and-tidy-dimensions.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [drawings-06-alternate-position-views](../entries/drawings/06-alternate-position-views.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [drawings-07-explode-lines-in-a-drawing-view](../entries/drawings/07-explode-lines-in-a-drawing-view.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [drawings-08-section-views-from-code](../entries/drawings/08-section-views-from-code.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [drawings-09-add-dimensions-and-tolerances](../entries/drawings/09-add-dimensions-and-tolerances.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [drawings-10-general-table](../entries/drawings/10-general-table.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [equations-01-global-variables-from-code](../entries/equations/01-global-variables-from-code.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [equations-02-link-a-dimension-to-a-global](../entries/equations/02-link-a-dimension-to-a-global.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-01-boss-extrude](../entries/features/01-boss-extrude.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-02-cut-extrude](../entries/features/02-cut-extrude.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-03-circular-pattern](../entries/features/03-circular-pattern.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-04-read-a-features-dimensions](../entries/features/04-read-a-features-dimensions.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-05-revolve](../entries/features/05-revolve.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-06-reference-plane-normal-to-a-line](../entries/features/06-reference-plane-normal-to-a-line.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-07-loft-cut](../entries/features/07-loft-cut.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-08-offset-reference-plane](../entries/features/08-offset-reference-plane.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-09-twisted-sweep](../entries/features/09-twisted-sweep.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-10-swept-cut](../entries/features/10-swept-cut.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [features-11-mirror-body](../entries/features/11-mirror-body.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [files-02-explode-configurations](../entries/files/02-explode-configurations.md) | “SolidWorks 2026 SP1.1” | verified | [34] |
| [files-03-upgrade-file-version](../entries/files/03-upgrade-file-version.md) | “SolidWorks 2026 SP1.1” | verified | [34] |
| [files-05-rename-a-component-file](../entries/files/05-rename-a-component-file.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [reading-01-dependencies-closed-file](../entries/reading/01-dependencies-of-a-closed-file.md) | “SolidWorks 2026” | verified | [34] |
| [reading-02-walk-reference-tree](../entries/reading/02-walk-a-reference-tree.md) | “SolidWorks 2026” | verified | [34] |
| [reading-03-repair-references](../entries/reading/03-repair-references-after-a-move.md) | *(none)* | unverified | [] |
| [reading-04-read-the-selection](../entries/reading/04-read-the-selection.md) | “SolidWorks 2026” | verified | [34] |
| [reading-05-sketch-to-model-transform](../entries/reading/05-sketch-to-model-transform.md) | “SolidWorks 2026” | verified | [34] |
| [reading-06-live-sketch-monitor](../entries/reading/06-live-sketch-monitor.md) | *(none)* | unverified | [] |
| [reading-07-report-feature-type-on-failure](../entries/reading/07-report-feature-type-on-failure.md) | “SolidWorks 2026” | verified | [34] |
| [reading-09-bounding-box](../entries/reading/09-bounding-box.md) | “SolidWorks 2026 SP1.1” | verified | [34] |
| [reading-10-mass-properties-as-an-oracle](../entries/reading/10-mass-properties-as-an-oracle.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [reading-11-cheap-change-detection](../entries/reading/11-cheap-change-detection.md) | “SolidWorks 2026” | verified | [34] |
| [reading-12-snapshot-suppression-before-you-suppress](../entries/reading/12-snapshot-suppression-before-you-suppress.md) | “SolidWorks 2026 SP0.0 (revision 34.0.0)” | verified | [34] |
| [reading-13-measure-a-wall-between-two-bodies](../entries/reading/13-measure-a-wall-between-two-bodies.md) | “SolidWorks 2026 SP0.0 (revision 34.0.0)” | verified | [34] |
| [reading-14-the-journal-records-api-calls](../entries/reading/14-the-journal-records-api-calls.md) | “SolidWorks 2026 SP0.0 (revision 34.0.0)” | verified | [34] |
| [reading-15-measure-a-part-that-has-no-dimensions](../entries/reading/15-measure-a-part-that-has-no-dimensions.md) | “SolidWorks 2024 SP5 (32.5.0)” | verified | [32] |
| [sketches-01-2d-sketch-as-vba](../entries/sketches/01-2d-sketch-as-vba.md) | “SolidWorks 2026 (revision 34.0.0)” | partly-verified | [34] |
| [sketches-03-relation-constants](../entries/sketches/03-relation-constants.md) | “SolidWorks 2026 (revision 34.0.0)” | partly-verified | [34] |
| [sketches-04-dimensions](../entries/sketches/04-dimensions.md) | “SolidWorks 2026 (revision 34.0.0)” | partly-verified | [34] |
| [sketches-07-equation-driven-curve](../entries/sketches/07-equation-driven-curve.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [sketches-10-is-the-sketch-fully-defined](../entries/sketches/10-is-the-sketch-fully-defined.md) | “SolidWorks 2026 (revision 34.0.0)” | verified | [34] |
| [surfacing-01-boundary-surface-recipe](../entries/surfacing/01-boundary-surface-recipe.md) | “SolidWorks 2026” | verified | [34] |
| [surfacing-02-axis-conventions](../entries/surfacing/02-axis-conventions.md) | “SolidWorks 2026” | verified | [34] |
| [surfacing-03-how-a-loft-fills-between-profiles](../entries/surfacing/03-how-a-loft-fills-between-profiles.md) | “SolidWorks 2026” | verified | [34] |
| [surfacing-04-cap-a-refused-loft-into-a-solid](../entries/surfacing/04-cap-a-refused-loft-into-a-solid.md) | “SolidWorks 2026 SP0.0 (revision 34.0.0)” | verified | [34] |
