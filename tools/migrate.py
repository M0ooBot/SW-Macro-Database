#!/usr/bin/env python3
"""One-off conversions of the v2 restructure, and the review lists they leave.

    python3 tools/migrate.py entries    # step 3: entry frontmatter to schema 2
    python3 tools/migrate.py gotchas    # step 4: GOTCHAS.md to gotchas/NNN-slug.md
    python3 tools/migrate.py ledger     # step 5: API-LEDGER.md to api-ledger.json

Each conversion copies what the source says and decides nothing silently:
wherever a value needed judgment, the choice and the source text it was made
from go in migration/review-*.md, for the owner to read and flag. The choices
themselves are the tables near the top of each section below, so the lists can
be regenerated. This file and migration/ are deleted once the lists are read.
Python 3 stdlib only.
"""

from __future__ import annotations

import pathlib
import re
import sys

import build_manifest
import gotchas as gotchas_mod
import ledger as ledger_mod
from frontmatter import format_value, read_frontmatter

ROOT = pathlib.Path(__file__).resolve().parent.parent
REVIEW = ROOT / "migration"


def md_cell(text) -> str:
    """Text for a markdown table cell, quoted as written."""
    if text is None:
        return "*(none)*"
    return str(text).replace("|", "\\|").replace("\n", " ")


def quote(text) -> str:
    return "*(none)*" if text is None else "“" + md_cell(text) + "”"


def majors_text(majors) -> str:
    return "[" + ", ".join(str(m) for m in majors) + "]"


# ==========================================================================
# step 3: entries

LANGUAGE_MAP = {"csharp": ["csharp-standalone"], "any": [], "n/a": []}

# Entries whose verified_on records no run: proposed unverified with no majors.
NO_RUN = {
    "connect-04-attach-vba": (
        "Records no run: \"standard across versions\" is a claim about the API, not an "
        "observation. Proposed unverified (the flag can choose partly-verified; verified needs "
        "an observation). The body's **Status:** line still says Verified: bodies are not edited "
        "here, so if the downgrade stands, a follow-up should change that line too."
    ),
    "sketches-06-sketch-api-limits": (
        "Records no run: \"documented API surface\" is the help's word, not an observation. "
        "Proposed unverified (the flag can choose partly-verified). The body's **Status:** line "
        "still says Verified: bodies are not edited here, so if the downgrade stands, a follow-up "
        "should change that line too."
    ),
}

# Majors that the main clause alone does not settle.
MAJORS_OVERRIDE = {
    "connect-05-choosing-among-versions": (
        [32, 34],
        "The main clause names a machine that carried three versions, not three runs. The body "
        "records runs on 2026 (choose()) and on 2024 SP5 (32.5.0: WrongVersion, and a read-only "
        "tool through find_candidates()), and says \"Not tried: 2025 (major 33)\".",
    ),
}

# Phrases that make a verified_on partial or indirect, so the row is shown for review.
PARTIAL = re.compile(r";| for | also |side by side|carrying|install|driven from|WSL2 to", re.I)


def main_clause(text: str) -> str:
    return text.split(";", 1)[0]


def entry_id_of(text: str) -> str:
    fm, _ = read_frontmatter(text)
    return fm["id"]


def convert_entry(text: str, new_values: dict) -> str:
    """The entry with its frontmatter rewritten as schema 2; the body is untouched.

    Kept keys keep their original text exactly; only the new keys are written.
    """
    end = text.find("\n---\n", 4)
    raw = {}
    for line in text[4:end].split("\n"):
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m:
            raw[m.group(1)] = m.group(2).strip()
    lines = []
    for key in build_manifest.KEYS_2:
        if key in new_values:
            lines.append(f"{key}: {format_value(new_values[key])}")
        else:
            lines.append(f"{key}: {raw[key]}")
    return "---\n" + "\n".join(lines) + text[end:]


def migrate_entries() -> int:
    judged, changed, copied = [], [], []
    for path in build_manifest.entry_paths(ROOT):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        old, problems = read_frontmatter(text)
        if problems or old is None:
            print(f"{rel}: cannot read frontmatter: {problems}", file=sys.stderr)
            return 1
        if old.get("schema") is not None:
            print(f"{rel}: already schema {old['schema']}", file=sys.stderr)
            return 1
        eid = old["id"]
        language = []
        for lang in old["language"]:
            language += LANGUAGE_MAP.get(lang, [lang])
        status = old["status"]
        verified_on = old.get("verified_on")
        parsed = sorted(build_manifest.majors_named(main_clause(verified_on))) if verified_on else []
        majors = parsed
        why = None
        if eid in NO_RUN:
            status, majors, why = "unverified", [], NO_RUN[eid]
            changed.append((rel, eid, verified_on, old["status"], status, majors, why))
        elif eid in MAJORS_OVERRIDE:
            majors, why = MAJORS_OVERRIDE[eid]
            judged.append((rel, eid, verified_on, status, parsed, majors, why))
        elif verified_on and (PARTIAL.search(verified_on) or len(parsed) > 1):
            if ";" in verified_on:
                why = "Only the main clause, before the semicolon, counts; what follows covers part of the claim."
            elif len(parsed) > 1:
                why = "The main clause names each of these versions for the whole claim."
            else:
                why = "The main clause names this version; the rest qualifies how or what, not where."
            judged.append((rel, eid, verified_on, status, parsed, majors, why))
        else:
            copied.append((rel, eid, verified_on, status, majors))
        new = convert_entry(text, {
            "schema": 2, "language": language, "status": status, "majors": majors,
            "evidence": [], "recipe_status": None, "recipe_evidence": [], "superseded_by": None,
        })
        fm, problems = read_frontmatter(new)
        same = all(fm[k] == old[k] for k in ("id", "title", "answers", "keywords", "api", "verified_on"))
        if problems or not same or new[new.find("\n---\n", 4):] != text[text.find("\n---\n", 4):]:
            print(f"{rel}: conversion did not keep the original values and body", file=sys.stderr)
            return 1
        path.write_text(new, encoding="utf-8")

    out = [
        "# Review list: entries (step 3)",
        "",
        "Every entry keeps its one `status` and its `verified_on` text, copied as written.",
        "`majors` is new: the revision majors (32 = SolidWorks 2024, 33 = 2025, 34 = 2026) that",
        "`verified_on` names, taken from its main clause only, with the most conservative",
        "value the text supports. Read the rows and flag only those you disagree with.",
        "Written by `tools/migrate.py entries`; the choices are its NO_RUN and MAJORS_OVERRIDE tables.",
        "",
        f"## Status changes proposed ({len(changed)})",
        "",
        "| Entry | Source text (`verified_on`) | Was | Proposed | Majors | Why |",
        "|---|---|---|---|---|---|",
    ]
    for rel, eid, von, was, now, majors, why in changed:
        out.append(f"| [{eid}](../{rel}) | {quote(von)} | {was} | **{now}** | {majors_text(majors)} | {md_cell(why)} |")
    out += [
        "",
        f"## Majors chosen with judgment ({len(judged)})",
        "",
        "The text is partial (a semicolon, \"also\", \"for the …\") or names several versions at once.",
        "",
        "| Entry | Source text (`verified_on`) | Status | Main clause gives | Chosen | Why |",
        "|---|---|---|---|---|---|",
    ]
    for rel, eid, von, status, parsed, majors, why in judged:
        out.append(f"| [{eid}](../{rel}) | {quote(von)} | {status} | {majors_text(parsed)} | "
                   f"**{majors_text(majors)}** | {md_cell(why)} |")
    out += [
        "",
        f"## Copied as parsed ({len(copied)})",
        "",
        "One version, stated plainly; the majors are that version. Listed so every entry is here.",
        "",
        "| Entry | Source text (`verified_on`) | Status | Majors |",
        "|---|---|---|---|",
    ]
    for rel, eid, von, status, majors in copied:
        out.append(f"| [{eid}](../{rel}) | {quote(von)} | {status} | {majors_text(majors)} |")
    REVIEW.mkdir(exist_ok=True)
    (REVIEW / "review-entries.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"entries: {len(changed)} status changes, {len(judged)} judged, {len(copied)} copied")
    return 0

# ==========================================================================
# step 4: gotchas

# The always-list: the silent, destructive and most common failure modes,
# proposed for the owner to confirm (P§14 Q2).
ALWAYS = {
    2: "Most common and silent: every length is metres and every angle radians, whatever the document says.",
    8: "Silent: a name set on collision becomes another name, and records point at nothing.",
    22: "Destructive: closing an upgraded older file can rewrite it in the new format, behind a misleading prompt.",
    25: "Silent: a new part can come out in inches from another year's template, and equations follow the units.",
    26: "Silent: Equation Manager calls fail by returning -1, never by raising.",
    34: "Destructive: SaveAs3 overwrites an existing file and reports success.",
    62: "Destructive and silent: suppression cascades, and unsuppressing does not bring the rest back.",
    93: "Common and costly: a full assembly rebuild marks every component modified, which turns closes into save prompts.",
    100: "Hangs: closing an assembly can raise a modal dialog (CAM add-in, older files) that blocks the script.",
    108: "Silent: every component handle goes stale after a configuration add or show, and answers wrongly instead of failing.",
}
NOT_ALWAYS = {
    9: "Rebuild once at the end: important, but about speed and transient errors, not silent damage.",
    10: "Transform rotation by columns: silent, but only for code that reads transform arrays.",
    23: "ShowConfiguration2 returning False: a false failure, not damage; G108 covers the dangerous part of configuration work.",
    51: "Clearing the selection during a user's pick crashed SolidWorks: severe, but only for code that polls the selection while the user works.",
    58: "EditRebuild3 returning False on any error: a misread that stops code, not silent damage.",
    95: "An over-defining mate is made anyway: silent, but specific to mate code.",
}

# Bindings, where a gotcha bites only some; every other gotcha is [all].
GOTCHA_LANGUAGES = {
    4: (["pywin32"], "Python: \"In Python, passing None fails\"; the fix is a pywin32 VARIANT."),
    5: (["pywin32","late-bound"], "Titled late-bound COM; observed through pywin32's dynamic dispatch. Early-bound C# calls methods as methods."),
    6: (["pywin32","late-bound"], "Late binding needs IDispatch; the code is pywin32."),
    7: (["csharp"], ".NET only: Marshal.GetActiveObject is gone on modern .NET."),
    21: (["late-bound","pywin32"], "VBScript and PowerShell (late-bound) fail; Python needs a typed VARIANT; VBA and early-bound C# work."),
    31: (["pywin32"], "pywin32 attribute access (the \"call\" helper); \"That pywin32 exposes…\"."),
    39: (["pywin32","late-bound"], "Titled late binding; observed through pywin32's dynamic dispatch."),
    40: (["pywin32","late-bound"], "\"through late binding\", Python method objects."),
    55: (["pywin32"], "\"a pywin32 late-binding point rather than a SolidWorks one\"."),
    74: (["pywin32"], "About swcom.py, this repo's Python attach module."),
    89: (["pywin32","late-bound"], "Titled late binding; observed through pywin32."),
}

# Member tags as chosen from the proposal (every backticked API name in the
# gotcha), with why, where the choice differs from the proposal.
GOTCHA_MEMBERS = {
    1: (["GetObject","GetActiveObject"], None),
    2: ([], None),
    3: (["InsertCurveFile"], None),
    4: (["ModifyDefinition","GetObjectByPersistReference3"], None),
    5: (["RevisionNumber","ActiveDoc","IAssemblyDoc.FixComponent","IBody2.GetEdges","IFace2.GetTessTriangles"], None),
    6: ([], None),
    7: (["GetActiveObject"], "GetRunningObjectTable and CreateBindCtx are the way round it, not the trap."),
    8: (["Name"], None),
    9: ([], None),
    10: (["IMathTransform.ArrayData"], None),
    11: (["InsertCurveFile"], None),
    12: (["InsertCompositeCurve"], None),
    13: (["InsertCurveFileBegin","LoadPointsFromFile"], None),
    14: (["InsertCurveFile"], None),
    15: ([], None),
    16: (["ReplaceReferencedDocument"], "GetOpenDocumentByName is the check it recommends, not the trap."),
    17: ([], None),
    18: (["IFeatureManager.MoveToFolder","InsertFeatureTreeFolder2"], None),
    19: (["FirstFeature","GetNextFeature","IFeatureFolder.GetFeatures","GetFirstSubFeature"], None),
    20: (["ISldWorks.OpenDoc6","ISldWorks.LoadFile4","OpenDoc7","GetOpenDocSpec"], "OpenDoc7 added: the text names it as no way out for STEP (it was not in the ledger, so the proposal missed it)."),
    21: (["OpenDoc6","LoadFile4"], None),
    22: (["ISldWorks.CloseDoc","QuitDoc","CloseAllDocuments"], "CloseAllDocuments added: the text names it as raising the prompt (not in the ledger, so the proposal missed it)."),
    23: (["ShowConfiguration2","DeleteConfiguration2","DeleteDesignTable","GetConfigurationNames"], "GetSaveFlag is how the side effect was observed, in passing."),
    24: (["IPartDoc.GetPartBox"], None),
    25: (["ISldWorks.GetDocumentTemplate"], "SetUserPreferenceInteger is the fix (set the units), not the trap."),
    26: (["IEquationMgr.Add3","Add2","IEquationMgr.SetEquationAndConfigurationOption"], "Equation(i) is the working alternative; Invoke is pywin32, not the API; Status is how -1 was read."),
    27: ([], None),
    28: ([], None),
    29: (["ISketchManager.CreateEquationSpline2"], None),
    30: (["sgEQUAL"], "sgEQUAL added: the backticked relation constant the gotcha is about (a constant, so not in the proposal)."),
    31: (["IAssemblyDoc.FixComponent"], "IsFixed is how the effect was checked, in passing."),
    32: (["IFeatureManager.FeatureCut4"], None),
    33: ([], None),
    34: (["IModelDocExtension.SaveAs3","IModelDoc2.SaveAs3"], None),
    35: (["GetStartPoint2","GetSelectedObjectCount2"], None),
    36: (["ISketchPoint.Select4"], "An observation, not a rule: SelectByID2 and GetSelectedObjectCount2 are the fallback and the check, and tagging them would show a one-off on every selection."),
    37: (["GetNextFeature","IFeature.GetFirstSubFeature","IFeature.GetNextSubFeature"], None),
    38: (["IFeatureManager.FeatureRevolve2"], "SelectByID2 is how the axis was selected (mark 16), in passing."),
    39: (["IMathUtility.CreateTransform"], "DISPATCH_METHOD is pywin32, not the API; IComponent2.Transform2 is where the result goes, in passing."),
    40: (["Done","GetInterferenceCount","GetInterferences","IInterference.Volume"], None),
    41: (["AddComponent5"], "Transform2 is the fix (set every frame), not the trap."),
    42: (["AddMate5"], None),
    43: (["IModelDoc2.AddDimension2"], None),
    44: (["IFeatureManager.InsertMoveCopyBody2"], "IBody2.Select2 is how the body was selected, in passing."),
    45: (["D1ReverseTwistDir","IFeatureManager.InsertProtrusionSwept4","InsertCutSwept5"], "GetDefinition, AccessSelections and ModifyDefinition are the ordinary route to the flag, not the trap."),
    46: (["IEquationMgr.Add2"], None),
    47: (["IFeatureManager.InsertMirrorFeature2","IBody2.Select2","ISelectionMgr.CreateSelectData"], None),
    48: ([], None),
    49: ([], None),
    50: ([], None),
    51: (["IModelDoc2.ClearSelection2"], "ISketchManager.ActiveSketch is the guard it recommends, not the trap."),
    52: ([], None),
    53: ([], None),
    54: (["FirstFeature","GetNextFeature"], "GetFeatureCount and GetUpdateStamp are the cheap alternative, not the trap."),
    55: (["ReleaseSelectionAccess","IBody2.GetEdges","IFace2.GetTessTriangles","IAssemblyDoc.FixComponent","IMassProperty.AddBodies","IModelDocExtension.DeleteDisplayStateSpecificRenderMaterial","IModelDocExtension.CreateBalloonOptions","IEdge.GetCurveParams2","IModelDoc2.EditRebuild3","INote.GetBalloonStyle","IMeasure.Calculate","ISldWorks.ExitApp"], "Dropped the members it lists as observed not to need this (GetFaces, GetBody, GetCurve, GetCurveParams2 on 2026, GetMassProperties, IsRolledBack, Name, GetTypeName2, GetNextFeature, InsertPlanarRefSurface) and DISPATCH_METHOD (pywin32)."),
    56: (["IFeature.ModifyDefinition","LoadPointsFromFile","ISldWorks.CommandInProgress","IFeatureManager.EditRollback"], None),
    57: (["IFeatureManager.EditRollback","IFeatureManager.GetRollbackBarPosition"], "FeatureByPositionReverse and IsRolledBack are the check it recommends."),
    58: (["EditRebuild3","ForceRebuild3"], None),
    59: (["AccessSelections","ReleaseSelectionAccess"], None),
    60: (["IModelDoc2.InsertPlanarRefSurface"], "IFace2.GetArea is the check it recommends."),
    61: (["IFeatureManager.InsertSewRefSurface"], "GetMassProperties and GetBodies2 are how it was detected."),
    62: (["IFeature.SetSuppression2"], "IsSuppressed is the snapshot it recommends."),
    63: (["InsertProtrusionBlend2"], None),
    64: ([], None),
    65: ([], None),
    66: (["InsertCurveFile","IModelDocExtension.GetLastFeatureAdded"], "GetFeatureCount and FeatureByName are named only as quick alternatives."),
    67: ([], None),
    68: (["IFeature.GetDefinition"], None),
    69: ([], "About the journal: Select2, Name, SaveAs and Save3 are examples of what it records, and tagging them would show this on every rename and save."),
    70: (["IModelDocExtension.DeleteDisplayStateSpecificRenderMaterial","IRenderMaterial.GetMaterialIds"], None),
    71: (["GetRenderMaterialsCount2"], None),
    72: ([], None),
    73: (["Transform2","EditRebuild3"], "GetErrorCode2 is how errors were read, in passing."),
    74: ([], None),
    75: (["GearRatioNumerator","IMate2.MateEntity","EntityParams"], None),
    76: (["GetFirstSubFeature","GetNextSubFeature","IMate2.Type"], None),
    77: (["IDrawingDoc.CreateDrawViewFromModelView3","ISheet.SetScale"], "UseSheetScale and ScaleDecimal are the fix and the check."),
    78: (["IView.InsertBomTable5","SetConfigurations"], "GetConfigurationCount is how the cause was read."),
    79: (["IModelDoc2.InsertNote"], "EditSheet and ClearSelection2 are the fix."),
    80: (["IAnnotation.Select3","EditDelete"], "GetAnnotation is how it was reached; SelectByID2 is the fix; ICenterMark.Select is a contrast."),
    81: (["IDrawingDoc.AutoBalloon5"], None),
    82: (["ReferencedConfiguration"], "ForceRebuild3 and ShowConfiguration2 are the fix."),
    83: (["AddMate5","Transform2"], "ForceRebuild3 is how a later measurement rebuilt, in passing."),
    84: (["EditDelete","InsertExplodeLineSketch"], None),
    85: (["UnblankSketch"], "SelectByID2 is how the sketch was selected, in passing."),
    86: (["IView.Position"], "ArrayData is the fix (read the model origin), in passing."),
    87: (["ISketchManager.CreateLine"], "IView.GetXform and IView.Angle are the conversion it recommends."),
    88: (["CreateSectionViewAt5"], "IView.Angle is the fix."),
    89: (["IView.GetVisibleEntities2","GetCurve","Select2"], None),
    90: (["ReplaceComponents2"], None),
    91: (["Text"], "Description is a custom property name, not a member; InsertColumn2 is the alternative."),
    92: (["AutoBalloon5","CreateBalloonOptions"], "InsertBOMBalloon2 and IBalloonOptions.ShowQuantity are the alternative that works."),
    93: (["ForceRebuild3"], "EditRebuild3 and Transform2 are the contrast (they did not mark everything); GetSaveFlag is how it was read."),
    94: (["AddMate5"], None),
    95: (["AddMate5","ForceRebuild3","GetErrorCode2"], "GetConstrainedStatus and GetWhatsWrongCount are the checks it recommends."),
    96: (["AddMate5","GearRatioNumerator","MateEntity"], None),
    97: (["IFeature.ModifyDefinition","CloseDoc"], None),
    98: (["Transform2","SetTransformAndSolve2","Drag","DragAsUI"], None),
    99: (["AddComponent5","OpenDoc6"], None),
    100: (["CloseDoc","QuitDoc"], "GetSaveFlag is how the state was read, in passing."),
    101: (["Drag"], "AddComponent, TransformType, UseAbsoluteTransform, DragMode and EndDrag are the recipe repeated, not the trap; a bare AddComponent would also match IAssemblyDoc.AddComponent."),
    102: (["OpenDoc6"], "GetSuppression2 is the check it recommends."),
    103: (["GetErrorCode2","SetSuppression2"], "GetSaveFlag is how the side effect was read."),
    104: ([], None),
    105: (["AddMate5","IGearMateFeatureData.Reverse","IMateEntity2.EntityParams"], "CommandInProgress is one condition tried, in passing."),
    106: (["AddMate5","IMateEntity2.EntityParams","IGearMateFeatureData.Reverse"], None),
    107: ([], None),
    108: (["AddConfiguration2","ShowConfiguration2","Transform2","IsFixed"], "GetComponentByName is the fix; DeleteConfiguration2 is the contrast (handles stayed good)."),
    109: (["IFeature.SetSuppression2","AddConfiguration2"], "IsSuppressed2 is the check it recommends."),
    110: (["GetSystemValue3","IDimension.SetSystemValue3","IDimension.SystemValue","IEquationMgr.Add2"], None),
    111: (["CreateSectionViewAt5","IView.GetSection","SetExcludedComponents"], "Invoke is pywin32, not the API."),
    112: (["ForceRebuild3","EditRebuild3"], "SaveAs is the export that showed it, in passing."),
    113: (["ShowConfiguration2","AddMate5"], None),
    114: (["ShowConfiguration2","ForceRebuild3"], "Name is the check; SetSuppression2 is a cross-reference."),
    115: (["ReferencedConfiguration"], None),
    116: (["Delete","Add2","Add3","SetEquationAndConfigurationOption"], None),
}

CODE_SPAN = re.compile(r"(?<!\x60)(\x60+)(?!\x60)(.+?)(?<!\x60)\1(?!\x60)", re.S)
LEADING_PATH = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
QUALIFIED = re.compile(r"(?<![A-Za-z0-9_.\x60])(I[A-Z][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)(?![A-Za-z0-9_])")


def code_spans(md: str) -> list[str]:
    lines = md.split("\n")
    text = "\n".join(l if o else "" for l, o in zip(lines, gotchas_mod.outside_fences(lines)))
    return [m.group(2).strip() for m in CODE_SPAN.finditer(text)]


def known_members() -> set[str]:
    """Lower-cased member names the database knows: the ledger's Member cells and every entry's api."""
    known = set()
    for e in build_manifest.collect(ROOT)[1]["entries"]:
        known |= {a.split(".")[-1].lower() for a in e["api"]}
    for line in (ROOT / "API-LEDGER.md").read_text(encoding="utf-8").split("\n"):
        if line.startswith("| ") and not line.startswith("| Member"):
            cell = re.split(r"(?<!\\)\|", line)[1]
            for span in code_spans(cell):
                m = LEADING_PATH.match(span)
                if m:
                    known.add(m.group(0).split(".")[-1].lower())
    return known


def propose_members(text: str, known: set[str]) -> list[str]:
    """Every backticked API name, Interface.Member where the text qualifies it, else Member."""
    found: list[str] = []
    for span in code_spans(text):
        m = LEADING_PATH.match(span)
        if not m:
            continue
        parts = m.group(0).split(".")
        qualified = len(parts) == 2 and re.match(r"^I[A-Z]", parts[0])
        if qualified or parts[-1].lower() in known:
            name = m.group(0) if qualified else parts[-1]
            if name not in found:
                found.append(name)
    for m in QUALIFIED.finditer(text):
        if m.group(0) not in found:
            found.append(m.group(0))
    # A bare name the text also gives with its interface is that qualified name.
    qualified_members = {f.split(".")[1] for f in found if "." in f}
    return [f for f in found if "." in f or f not in qualified_members]


def split_gotchas(text: str) -> list[dict]:
    if not text.startswith(gotchas_mod.PREAMBLE):
        raise ValueError("GOTCHAS.md does not start with the preamble gotchas.py holds")
    lines = text.split("\n")
    outside = gotchas_mod.outside_fences(lines)
    heads = [(i, int(m.group(1)), m.group(2)) for i, l in enumerate(lines) if outside[i]
             for m in [re.match(r"^## (\d+)\. (.+)$", l)] if m]
    found = []
    for k, (i, n, title) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        if lines[i + 1] != "":
            raise ValueError(f"gotcha {n}: no blank line after its heading")
        body = "\n".join(lines[i + 2:end]).rstrip("\n") + "\n"
        found.append({"number": n, "id": f"G{n}", "title": title, "always": n in ALWAYS,
                      "path": f"gotchas/{n:03d}-{gotchas_mod.slug(title)}.md", "body": body})
    return found


def migrate_gotchas() -> int:
    source = (ROOT / "GOTCHAS.md").read_text(encoding="utf-8")
    found = split_gotchas(source)
    if [g["number"] for g in found] != list(range(1, len(found) + 1)) or set(GOTCHA_MEMBERS) != {g["number"] for g in found}:
        print("GOTCHAS.md numbers and the GOTCHA_MEMBERS table do not match 1..N", file=sys.stderr)
        return 1
    known = known_members()
    rows = []
    for g in found:
        n = g["number"]
        proposed = propose_members(g["title"] + "\n\n" + g["body"], known)
        g["members"], why = GOTCHA_MEMBERS[n]
        g["languages"] = GOTCHA_LANGUAGES.get(n, (["all"], None))[0]
        rows.append((g, proposed, why))
    for g in found:
        g["body"] = gotchas_mod.file_links(g["body"], found)
    if gotchas_mod.render_md(found) != source:
        print("the generated GOTCHAS.md would differ from the original; nothing written", file=sys.stderr)
        return 1
    (ROOT / "gotchas").mkdir(exist_ok=True)
    for g in found:
        front = "\n".join(f"{k}: {format_value(g[k])}" for k in gotchas_mod.KEYS)
        (ROOT / g["path"]).write_text(f"---\n{front}\n---\n\n{g['body']}", encoding="utf-8")
    problems, loaded = gotchas_mod.load(ROOT)
    if problems or gotchas_mod.render_md(loaded) != source:
        print("the written files do not read back to the original:", *problems, sep="\n  ", file=sys.stderr)
        return 1

    def link(g):
        return f"[G{g['number']}](../{g['path']})"

    out = [
        "# Review list: gotchas (step 4)",
        "",
        "GOTCHAS.md is now generated from one file per gotcha, `gotchas/NNN-slug.md`, numbers",
        "kept; the generated file was checked equal to the original before it was replaced.",
        "Three things are new and need your eye: the always-list, the bindings a gotcha is",
        "tagged with, and the member tags. Flag only the rows you disagree with.",
        "Written by `tools/migrate.py gotchas` from its ALWAYS, GOTCHA_LANGUAGES and GOTCHA_MEMBERS tables.",
        "",
        f"## The always-list: please confirm ({len(ALWAYS)})",
        "",
        "Rendered into the `sw-macro-database` skill and SW-Agent's own skill, and returned by",
        "`gotchas_for(topic: \"always\")`. Chosen for silent, destructive or most common failure modes.",
        "",
        "| Gotcha | Title | Why always |",
        "|---|---|---|",
    ]
    by_n = {g["number"]: g for g in found}
    out += [f"| {link(by_n[n])} | {md_cell(by_n[n]['title'])} | {md_cell(why)} |" for n, why in sorted(ALWAYS.items())]
    out += ["", "Considered and not proposed:", "", "| Gotcha | Title | Why not |", "|---|---|---|"]
    out += [f"| {link(by_n[n])} | {md_cell(by_n[n]['title'])} | {md_cell(why)} |" for n, why in sorted(NOT_ALWAYS.items())]
    out += [
        "",
        f"## Bindings other than `all` ({len(GOTCHA_LANGUAGES)})",
        "",
        "`languages` says how the API must be bound for the gotcha to bite: `all`, `csharp`, `pywin32`",
        "or `late-bound`. Every gotcha not listed here is `[all]`: when the text does not limit it, it",
        "is shown to everyone. SW-Agent's `gotchas_for` filters on this (C# by default).",
        "",
        "| Gotcha | Title | Chosen | Why |",
        "|---|---|---|---|",
    ]
    out += [f"| {link(by_n[n])} | {md_cell(by_n[n]['title'])} | {majors_text(langs)} | {md_cell(why)} |"
            for n, (langs, why) in sorted(GOTCHA_LANGUAGES.items())]
    changed = [r for r in rows if r[0]["members"] != r[1]]
    out += [
        "",
        f"## Member tags ({len(rows)}; {len(changed)} differ from the proposal)",
        "",
        "Proposed: every backticked API name in the gotcha (a name the ledger or an entry's `api`",
        "knows, or one written `Interface.Member`), qualified where the gotcha writes the interface.",
        "Chosen: the proposal less the names the gotcha only mentions in passing (the check it",
        "recommends, the fix, a contrast), so `gotchas_for` on a common member does not return every",
        "gotcha that happens to name it. When in doubt a tag was kept: a missing tag hides a warning.",
        "",
        "| Gotcha | Proposed (from the text) | Chosen | Why |",
        "|---|---|---|---|",
    ]
    for g, proposed, why in rows:
        same = g["members"] == proposed
        out.append(f"| {link(g)} | {md_cell(', '.join(proposed)) if proposed else '*(none)*'} | "
                   f"{'same' if same else ('**' + md_cell(', '.join(g['members'])) + '**' if g['members'] else '**(none)**')} | "
                   f"{md_cell(why) if why else ''} |")
    REVIEW.mkdir(exist_ok=True)
    (REVIEW / "review-gotchas.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"gotchas: {len(found)} files written, {len(ALWAYS)} always, {len(changed)} member lists changed from the proposal")
    return 0

# ==========================================================================
# step 5: the API ledger

# Status cells whose wording is not a plain "Verified …", "Unverified …" or
# "Partly verified …", with the status chosen and why.
LEDGER_STATUS = {
    "Observed once (the dialog), SW 2024 SP5 (32.5.0), 2026-11-02; the `0x80010105` verified, tier 7/8 2026-11-13/14": (
        "fails", "Both halves are failures seen (a hang on a dialog, once; the 0x80010105 exception), on 2024; the note keeps \"observed once\"."),
    "Verified; crash observed, Airfoil Converter 2026-09-16": (
        "verified", "The call works; the crash is a condition (a user's pick), which the note and purpose keep."),
    "Ran, SW 2024 (32.5.0), 2026-10-01": (
        "partly-verified", "It ran without error; whether it redraws (its purpose) was not observed."),
    "Read, SW 2024 (32.5.0), 2026-10-01": (
        "partly-verified", "It was read; what the value means is not known."),
    "Set, SW 2026 SP0.0, Airfoil Converter 2026-09-23": (
        "partly-verified", "It was set; its effect on graphics was not observed, only that it did not speed a reload."),
    "Verified for 1 and 4, verified not to work for 2, SW 2026 SP0.0, Airfoil Converter 2026-09-22": (
        "partly-verified", "Two actions work and one does not, for one call form: neither verified nor fails as a whole."),
    "Verified for item 3, SW 2026 SP0.0, Airfoil Converter 2026-09-22": (
        "partly-verified", "One item of the twelve is identified; the rest were not."),
    "Verified on a line, SW 2026 (34.0.0)": (
        "partly-verified", "Verified on a line only; the purpose says other entities vary by version."),
    "Verified, SW 2024 SP5 (32.5.0), 2026-10-28 (read only)": (
        "partly-verified", "Read only, and the purpose says the meanings were not checked."),
    "Verified, SW 2024 SP5 (32.5.0), 2026-10-28 (value suspect)": (
        "partly-verified", "The cell itself calls the value suspect."),
    "Verified, SW 2024 SP5 (32.5.0), 2026-11-09; exclusion not reproduced 2026-11-15": (
        "partly-verified", "A later run found the exclusion array ignored (GOTCHAS §111), so part of the form is not reliable."),
    "Verified not to carry through gear or lock mates on that train, Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), tier 7/8 2026-11-13/14": (
        "fails", "Observed not to do what the row is about (carry a drag through the train)."),
    "Verified absent, Verified, SW 2026 (34.1.1) and SW 2024 SP5 (32.5.0), tier 7/8 2026-11-13/14": (
        "absent", "Observed not to exist on both versions."),
}

# Majors for cells that name no version of their own, from the preamble's
# account of the run they cite.
LEDGER_MAJORS = {
    "Verified; crash observed, Airfoil Converter 2026-09-16": (
        [34], "The preamble: rows marked \"Airfoil Converter 2026-09-16\" come from that tool's work on SolidWorks 2026."),
}

PLAIN = {"Verified": "verified", "Unverified": "unverified", "Partly verified": "partly-verified"}
VERSION_SEGMENT = re.compile(r"\bSW \d{4}|\bSolidWorks\b|\b\d\d\.\d+\.\d+\b")


def split_cells(line: str) -> list[str]:
    cells = re.split(r"(?<!\\)\|", line.strip())[1:-1]
    return [c.strip().replace("\\|", "|") for c in cells]


def top_level_split(text: str) -> list[str]:
    """Split on ", " outside parentheses."""
    out, depth, cur = [], 0, ""
    i = 0
    while i < len(text):
        ch = text[i]
        depth += ch == "("
        depth -= ch == ")"
        if depth == 0 and text.startswith(", ", i):
            out.append(cur)
            cur = ""
            i += 2
            continue
        cur += ch
        i += 1
    return out + [cur]


def ledger_status(cell: str):
    """(status, note, why or None) for a Status cell."""
    if cell in LEDGER_STATUS:
        status, why = LEDGER_STATUS[cell]
        return status, cell, why
    if cell == "Verified":
        return "verified", ledger_mod.NO_VERSION, None
    if cell in PLAIN:
        return PLAIN[cell], None, None
    if cell.startswith("Verified not to work"):
        return "fails", cell, None
    if cell.startswith("Verified absent"):
        return "absent", cell, None
    for word, status in (("Partly verified", "partly-verified"), ("Unverified", "unverified"), ("Verified", "verified"),
                         ("Put verified", "verified")):
        if cell.startswith(word):
            return status, cell, None
    raise ValueError(f"status cell {cell!r} matches no rule; add it to LEDGER_STATUS")


def ledger_majors(cell: str, status: str):
    if status == "unverified":
        return [], None
    if cell in LEDGER_MAJORS:
        return LEDGER_MAJORS[cell]
    main = cell.split(";", 1)[0]
    majors = build_manifest.majors_named(main) or build_manifest.majors_named(cell)
    return sorted(majors), None


def ledger_provenance(cell: str):
    main = cell.split(";", 1)[0]
    if len(top_level_split(main)) < 2:
        main = cell
    segs = top_level_split(main)
    last = max((i for i, s in enumerate(segs) if VERSION_SEGMENT.search(s)), default=0)
    rest = ", ".join(segs[last + 1:]).strip()
    rest = re.sub(r"\s*\([^()\d]*\)$", "", rest)
    return rest or None


def section_interface(title: str):
    subject = title.split(" (", 1)[0]
    names = re.findall(r"\bI[A-Z][A-Za-z0-9_]*", subject)
    return names[0] if len(names) == 1 else None


def row_members(form: str, interface):
    """Every backticked name in a Member cell, qualified where the cell or the heading says.

    A cell that writes an Interface.Member gives no interface to its other
    names (they may be another object's, or pywin32's); only a cell that
    names no interface takes the heading's.
    """
    paths = [m.group(0) for span in code_spans(form) for m in [LEADING_PATH.match(span)] if m]
    def qualified(p):
        parts = p.split(".")
        return len(parts) == 2 and re.match(r"^I[A-Z]", parts[0])
    cell_names_one = any(qualified(p) for p in paths)
    out = []
    for path in paths:
        parts = path.split(".")
        if qualified(path):
            name = path
        elif len(parts) == 1 and interface and not cell_names_one:
            name = f"{interface}.{parts[0]}"
        else:
            name = parts[-1]
        if name not in out:
            out.append(name)
    return out


def parse_ledger(text: str):
    if not text.startswith(ledger_mod.TITLE):
        raise ValueError("API-LEDGER.md does not start with the title ledger.py holds")
    body = text[len(ledger_mod.TITLE):]
    first = body.find("\n## ")
    preamble, rest = body[:first], body[first + 1:]
    sections, rows = [], []
    for block in re.split(r"(?m)^## ", rest)[1:]:
        title, _, content = block.partition("\n")
        lines = content.strip("\n").split("\n")
        table_at = next((i for i, l in enumerate(lines) if l.startswith("| ")), None)
        note_lines = lines if table_at is None else lines[:table_at]
        note = "\n".join(note_lines).strip("\n") or None
        sections.append({"title": title, "note": note})
        if table_at is None:
            continue
        header = split_cells(lines[table_at])
        interface = section_interface(title)
        for line in lines[table_at + 2:]:
            if not line.startswith("|"):
                raise ValueError(f"section {title!r}: text after its table")
            cells = dict(zip(header, split_cells(line)))
            status, note_text, _ = ledger_status(cells["Status"])
            majors, _ = ledger_majors(cells["Status"], status)
            rows.append({
                "section": title,
                "interface": interface,
                "members": row_members(cells["Member"], interface),
                "form": cells["Member"],
                "purpose": cells["Purpose"],
                "on": cells.get("On"),
                "status": status,
                "note": note_text,
                "provenance": ledger_provenance(cells["Status"]) if cells["Status"] not in PLAIN else None,
                "languages": ["pywin32"] if "from Python" in cells["Status"] else [],
                "majors": majors,
                "evidence": [],
                "_cell": cells["Status"],
            })
    return {"schema": 1, "preamble": preamble, "sections": sections, "rows": rows}


def migrate_ledger() -> int:
    source = (ROOT / "API-LEDGER.md").read_text(encoding="utf-8")
    data = parse_ledger(source)
    cells = [r.pop("_cell") for r in data["rows"]]
    problems = ledger_mod.check(data, set())
    if problems:
        print("the converted ledger does not check:", *problems, sep="\n  ", file=sys.stderr)
        return 1
    if ledger_mod.render_md(data) != source:
        print("the generated API-LEDGER.md would differ from the original; nothing written", file=sys.stderr)
        return 1
    (ROOT / "api-ledger.json").write_text(ledger_mod.render_json(data), encoding="utf-8")

    rows = data["rows"]
    by_cell: dict[str, list[int]] = {}
    for i, c in enumerate(cells):
        by_cell.setdefault(c, []).append(i)
    out = [
        "# Review list: API ledger (step 5)",
        "",
        "API-LEDGER.md is now generated from `api-ledger.json`, one row per call form as before; the",
        "generated file was checked equal to the original before it was replaced. Each row gains a",
        "status from the fixed set (verified, partly-verified, unverified, fails, absent), the cell's",
        "own wording as `note`, the run it cites as `provenance`, `majors`, `members` and `interface`.",
        "Flag only the rows you disagree with. Written by `tools/migrate.py ledger` from its",
        "LEDGER_STATUS and LEDGER_MAJORS tables and the rules below.",
        "",
        f"## Status cells that needed a decision ({len(LEDGER_STATUS)})",
        "",
        "| Status cell (source) | Rows | Member | Chosen status | Majors | Why |",
        "|---|---|---|---|---|---|",
    ]
    for cell, (status, why) in LEDGER_STATUS.items():
        idx = by_cell.get(cell, [])
        forms = "; ".join(rows[i]["form"] for i in idx)
        majors = rows[idx[0]]["majors"] if idx else []
        extra = f" Majors: {LEDGER_MAJORS[cell][1]}" if cell in LEDGER_MAJORS else ""
        out.append(f"| {quote(cell)} | {len(idx)} | {md_cell(forms)} | **{status}** | {majors_text(majors)} | {md_cell(why + extra)} |")
    bare = [i for i, c in enumerate(cells) if c == "Verified"]
    out += [
        "",
        f"## \"Verified\" and nothing more ({len(bare)})",
        "",
        "The source says verified and names no version or run. Proposed `verified`, `majors: []`,",
        f"`note: \"{ledger_mod.NO_VERSION}\"`: the cell still reads \"Verified\", and SW-Agent's `api_status`",
        "shows the note. Flag a row to have it downgraded instead.",
        "",
        "| Section | Member | Purpose |",
        "|---|---|---|",
    ]
    out += [f"| {md_cell(rows[i]['section'])} | {md_cell(rows[i]['form'])} | {md_cell(rows[i]['purpose'])} |" for i in bare]
    out += [
        "",
        "## Every status cell, as read (rules)",
        "",
        "Rules: \"Verified not to work …\" is `fails`; \"Verified absent …\" is `absent`; otherwise the",
        "first words give the status. `majors` are the versions the cell names before any semicolon",
        "(after it only when nothing before it names one); none for `unverified`. `provenance` is",
        "what follows the last version named (the run), or `null`. `languages` is `[pywin32]` where the",
        "cell says \"from Python\", else `[]` (the row does not say).",
        "",
        "| Status cell (source) | Rows | Status | Majors | Provenance | Languages |",
        "|---|---|---|---|---|---|",
    ]
    for cell, idx in sorted(by_cell.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        r = rows[idx[0]]
        out.append(f"| {quote(cell)} | {len(idx)} | {r['status']} | {majors_text(r['majors'])} | "
                   f"{quote(r['provenance'])} | {majors_text(r['languages'])} |")
    out += [
        "",
        "## Interface by section",
        "",
        "A section's `interface` is the one interface its heading names before any parenthesis;",
        "`null` when it names none or several. A row's bare members take that interface only when",
        "the Member cell names none itself: in a cell such as `ITableAnnotation.RowCount` / `ColumnCount`",
        "the other names stay bare. A dotted path that does not start with an interface",
        "(`Dimension.Name`, `IDimension.Tolerance.Type`) is kept as its last name only. One heading to",
        "look at: 'IBomFeature and the table' gives IBomFeature to its rows that name no interface",
        "(`GetConfigurationCount`, `SetConfigurations`, `FollowAssemblyOrder2`, `TableType`).",
        "",
        "| Section (source) | Rows | Interface |",
        "|---|---|---|",
    ]
    for s in data["sections"]:
        n = sum(1 for r in rows if r["section"] == s["title"])
        out.append(f"| {quote(s['title'])} | {n} | {section_interface(s['title']) or '*(null)*'} |")
    no_members = [r for r in rows if not r["members"]]
    odd = [r for r in rows if any("." in c and c.count(".") > 1 or (c.split(".")[0] and not c.split(".")[0].startswith("I") and "." in c)
                                  for c in re.findall(r"\x60([A-Za-z_][\w.]*)", r["form"]))]
    out += [
        "",
        "## Rows whose members need a look",
        "",
        "| Section | Member cell (source) | Members | Why |",
        "|---|---|---|---|",
    ]
    out += [f"| {md_cell(r['section'])} | {md_cell(r['form'])} | *(none)* | No backticked name in the cell, so `api_status` cannot reach the row by member; it stays in API-LEDGER.md. |" for r in no_members]
    out += [f"| {md_cell(r['section'])} | {md_cell(r['form'])} | {md_cell(', '.join(r['members']))} | A dotted path not of the form Interface.Member: its last name only. |" for r in odd]
    REVIEW.mkdir(exist_ok=True)
    (REVIEW / "review-ledger.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"ledger: {len(rows)} rows in {len(data['sections'])} sections, {counts}, "
          f"{sum(1 for r in rows if r['interface'])} rows with an interface")
    return 0


# ==========================================================================

COMMANDS = {"entries": migrate_entries, "gotchas": migrate_gotchas, "ledger": migrate_ledger}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in COMMANDS:
        print(f"usage: migrate.py {{{'|'.join(COMMANDS)}}}", file=sys.stderr)
        return 2
    return COMMANDS[argv[0]]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
