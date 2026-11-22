---
schema: 2
id: files-06-export-loaded-solid-part-to-stl
title: Export a loaded solid part as binary STL
answers: "How do I export a part already loaded by a SolidWorks assembly as a binary STL without activating it?"
keywords: [STL, binary STL, mesh, tessellation, loaded assembly reference, invisible part, GetTessellation, GetFacetFins, GetFinVertices, millimetres, 3D printing]
api: [ISldWorks.GetOpenDocumentByName, IModelDoc2.ConfigurationManager, IConfigurationManager.ActiveConfiguration, IPartDoc.GetBodies2, IBody2.GetTessellation, ITessellation.Tessellate, ITessellation.GetFacetCount, ITessellation.GetFacetFins, ITessellation.GetFinVertices, ITessellation.GetVertexCount, ITessellation.GetVertexPoint, ITessellation.GetVertexNormal]
language: []
status: verified
verified_on: SolidWorks 2024 SP5 (32.5.0), C# in the SW-Agent worker
majors: [32]
evidence: []
recipe_status: verified
recipe_evidence: [2026-11-22-files-06-export-loaded-solid-part-to-stl-csharp-32, 2026-11-22-files-06-export-loaded-solid-part-to-stl-csharp-32-smoke, 2026-11-22-files-06-export-loaded-solid-part-to-stl-csharp-32-preflight]
superseded_by: null
---

# Export a loaded solid part as binary STL

The [C# recipe](06-export-loaded-solid-part-to-stl.csx) reads the solid bodies of a part already loaded through an assembly and returns a binary STL payload. It runs through SW-Agent on the SolidWorks worker's STA, including when the part is invisible in the session.

## Read the loaded part

Pass the part's full path and the assembly occurrence's referenced configuration. The recipe looks up the existing document through **ISldWorks.GetOpenDocumentByName** and checks **IConfigurationManager.ActiveConfiguration** via **IModelDoc2.ConfigurationManager**. A mismatch stops the read. The same file can occur in more than one configuration, so use path and referenced configuration together when grouping occurrences for quantity-suffixed output files. The recipe emits part-local coordinates.

**IPartDoc.GetBodies2** reads all solid bodies, including hidden solid bodies. For each body, **IBody2.GetTessellation** creates an **ITessellation**. The recipe sets facet topology matching, requests vertex normals, and sets chord and plane tolerances of 0.00002 m (0.02 mm) and angle tolerances of π/36 radians (5°) before calling **ITessellation.Tessellate**. **ITessellation.GetFacetFins** and **GetFinVertices** give each triangle's three vertex indices. **ITessellation.GetVertexPoint** supplies coordinates in metres. Convert them to millimetres, and use **ITessellation.GetVertexNormal** to orient each facet before calculating its STL normal.

The result includes counts, signed mesh volume in mm³, and a gzip-compressed, base64-encoded binary STL under **gzipStlBase64**. Decode base64 and decompress gzip outside SolidWorks. STL has no units field, so configure the consumer to interpret the coordinates as millimetres. A part with zero solid bodies returns a null payload. For a large response, use the bridge's fullResultPath. Meshes beyond the worker's result limits require a different transfer method. For a nonempty result, check the little-endian triangle count at offset 80 and the exact file size of 84 + 50 × triangle count before writing to a new output path.

## Referenced parts and the SW-Agent read gate

The read requires a loaded part in the requested configuration and accessible solid bodies. Unresolved, suppressed, surface-only, or reference-only components can require a different workflow. When a loaded part has an in-context dependency back to an open assembly, SW-Agent's raw read preflight can refuse the call before the recipe executes. Record that refusal as a skipped export and preserve the assembly session.

## Native STL export and import

According to the SolidWorks API documentation, native STL export is **IModelDocExtension.SaveAs3** with a full .stl path, using **ISldWorks.ActivateDoc3** and **ISldWorks.ActiveDoc** to make and verify the source as active. **IModelDoc2.ClearSelection2** clears any face or body selection for whole-model output. **SaveAs3** can overwrite an existing file. Native STL preferences govern the output unit, binary or ASCII format, resolution, and translation to positive space. Activating documents and invoking Save As require a guarded write in SW-Agent. Native translator behavior on hidden assembly references is still unverified. [SaveAs3 API](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDocExtension~SaveAs3.html?format=P&value=) · [SolidWorks 2024 STL conversion options](https://help.solidworks.com/2024/english/EnterprisePDM/Admin/IDD_CONVOPSTLDLG.htm?id=2.24.4.0.9)

SolidWorks 2024 opens STL through **File > Open > Mesh Files**. Set the source unit and choose a graphics, surface, or solid body. Closed meshes can become solids. Meshes that cannot close may import as surfaces. The native import and export paths are documented capabilities. The evidence here covers extracting and encoding the tessellation. [Importing mesh files](https://help.solidworks.com/2024/english/SolidWorks/sldworks/t_importing_mesh_file.htm) · [STL import API preferences](https://help.solidworks.com/2024/english/api/swconst/fileopenoptionsstlvrml.htm)

## Evidence

On SolidWorks 2024 SP5 (32.5.0), seven loaded parts returned one solid each, with 2,812 to 47,088 triangles per STL. An independent decoder verified the exact binary length, finite points, nonzero extents in all three axes, unit normals, zero degenerate facets, and zero boundary or nonmanifold edges using exact stored vertices. A reference-only part returned zero solid bodies and a null payload. Two in-context back-references were refused by raw read preflight before execution. A second smoke run through SW-Agent used the exact sidecar and reproduced the seven payloads, the empty result, and both preflight refusals.

## See also

- [files/04 — Write one body of a part to STEP](04-export-a-body-to-step.md)
- [files/01 — Batch-convert STEP to SolidWorks parts](01-batch-convert-step.md)
- [connect/07 — Find the open document](../connect/07-find-the-open-document.md)
- [GOTCHAS §34](../../gotchas/034-saveas3-overwrites-an-existing-file-without-a.md)
