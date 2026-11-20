#!/usr/bin/env python3
"""The CI gate. Run from anywhere:

    python3 tools/validate.py

Exits non-zero and lists every problem found. It checks, in order:

  1. every entry, gotcha, evidence record and ledger row, with the same checks
     tools/build_manifest.py applies, and that the committed manifest.json,
     gotchas.json, GOTCHAS.md and API-LEDGER.md are exactly what
     build_manifest.py would write;
  2. every scripts/<id>/ folder: script.json shape (strict, no unknown keys) and
     a lint of script.csx;
  3. every skills/<name>/ folder: SKILL.md frontmatter, and the template's
     placeholders;
  4. that the release package builds (into a temp dir, version 0.0.0-ci),
     and search: the packaged lookup.py, run on the extracted package, passes
     search-tests.json (match-text vectors and test questions; needs FTS5);
  5. that the release notes can be written (against the latest v* tag, when
     the clone has it), so a broken tag workflow shows here, not at release;
  6. the unit tests in tools/tests/.

Python 3 stdlib only.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import pathlib
import re
import sys
import tempfile
import unittest
import zipfile

import build_manifest
import build_package
import evidence as evidence_mod
import recipes
import textfile

ROOT = pathlib.Path(__file__).resolve().parent.parent

STATUSES = build_manifest.CLAIMS
EFFECTS = recipes.EFFECTS
PARAM_TYPES = recipes.PARAM_TYPES
ROLES = recipes.ROLE_NAMES

SCRIPT_KEYS = {"id", "title", "entry", "status", "evidence", "effects", "irreversible",
               "supportsDryRun", "timeoutMinutes", "openTargets", "params"}
PARAM_KEYS = {"name", "type", "required", "description", "role", "default"}

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CAMEL = recipes.CAMEL

# Scripts run unattended inside someone's SolidWorks session. These are the
# ways a script can reach outside it, hang it, or hide from the host.
CSX_FORBIDDEN = [
    ("GetActiveObject", re.compile(r"GetActiveObject")),
    ("Activator.CreateInstance", re.compile(r"Activator\.CreateInstance")),
    ("GetTypeFromProgID", re.compile(r"GetTypeFromProgID")),
    ("CloseAllDocuments", re.compile(r"CloseAllDocuments")),
    ("Process.Start", re.compile(r"Process\.Start")),
    ("HttpClient", re.compile(r"HttpClient")),
    ("WebClient", re.compile(r"WebClient")),
    ("System.Net", re.compile(r"System\.Net")),
    ("Environment.Exit", re.compile(r"Environment\.Exit")),
    ("await", re.compile(r"\bawait\b")),
    ("#r directive", re.compile(r"^\s*#r\s")),
    ("#load directive", re.compile(r"^\s*#load\s")),
]

# A script with openTargets: true runs on documents the user may have open, so
# it opens and closes only through Kit.Docs, which never closes what it did not
# open. These are the direct calls that could.
CSX_FORBIDDEN_WITH_OPEN_TARGETS = [
    (name, re.compile(r"\b" + name + r"\b")) for name in ("OpenDoc6", "OpenDoc7", "LoadFile4", "CloseDoc", "QuitDoc")
]


# --------------------------------------------------------------------------
# scripts


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _default_ok(ptype: str, v) -> bool:
    if ptype in ("string", "file", "folder"):
        return isinstance(v, str)
    if ptype == "bool":
        return isinstance(v, bool)
    if ptype == "int":
        return _is_int(v)
    if ptype == "number":
        return _is_number(v)
    if ptype == "files":
        return isinstance(v, list) and all(isinstance(x, str) for x in v)
    return False


def _no_duplicate_keys(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError(f"duplicate key {k!r}")
        obj[k] = v
    return obj


def check_params(where: str, effects, params) -> list[str]:
    problems: list[str] = []
    if not isinstance(params, list):
        return [f"{where}: 'params' must be a list"]
    seen: set[str] = set()
    roles: dict[str, list[str]] = {"targets": [], "output": []}
    for i, p in enumerate(params):
        tag = f"{where}: params[{i}]"
        if not isinstance(p, dict):
            problems.append(f"{tag} must be an object")
            continue
        for k in sorted(set(p) - PARAM_KEYS):
            problems.append(f"{tag}: unknown key '{k}'")
        name = p.get("name")
        if not isinstance(name, str) or not CAMEL.match(name):
            problems.append(f"{tag}: 'name' must be a camelCase identifier, got {name!r}")
        else:
            tag = f"{where}: param '{name}'"
            if name in seen:
                problems.append(f"{tag}: duplicate param name")
            seen.add(name)
        ptype = p.get("type")
        if ptype not in PARAM_TYPES:
            problems.append(f"{tag}: 'type' {ptype!r} is not one of {sorted(PARAM_TYPES)}")
        if not isinstance(p.get("required"), bool):
            problems.append(f"{tag}: 'required' must be true or false")
        desc = p.get("description")
        if not isinstance(desc, str) or not desc.strip():
            problems.append(f"{tag}: 'description' must be a non-empty string")
        if "role" in p:
            role = p["role"]
            if role not in ROLES:
                problems.append(f"{tag}: 'role' {role!r} is not one of {sorted(ROLES)}")
            else:
                roles[role].append(name if isinstance(name, str) else f"params[{i}]")
                if role == "targets" and ptype not in ("file", "files"):
                    problems.append(f"{tag}: role 'targets' needs type file or files")
                if effects == "read-only" and role == "targets" and p.get("required") is not True:
                    problems.append(f"{tag}: role 'targets' must be required for a read-only script")
                if role == "output" and ptype != "folder":
                    problems.append(f"{tag}: role 'output' needs type folder")
        if "default" in p and ptype in PARAM_TYPES and not _default_ok(ptype, p["default"]):
            problems.append(f"{tag}: 'default' {p['default']!r} is not a valid {ptype}")

    if effects == "modifies-models" and len(roles["targets"]) != 1:
        problems.append(f"{where}: a modifies-models script needs exactly one param with role "
                        f"'targets' (found {len(roles['targets'])})")
    if effects == "edits-open-document" and (len(roles["targets"]) != 1 or roles["output"]):
        problems.append(f"{where}: an edits-open-document script needs exactly one param with role "
                        f"'targets' and none with role 'output' (it saves nothing)")
    if effects == "writes-new-files" and len(roles["output"]) != 1:
        problems.append(f"{where}: a writes-new-files script needs exactly one param with role "
                        f"'output' (found {len(roles['output'])})")
    if effects == "read-only" and (len(roles["targets"]) > 1 or roles["output"]):
        problems.append(f"{where}: a read-only script allows at most one param with role "
                        f"'targets' and none with role 'output'")
    return problems


def check_script_json(root: pathlib.Path, folder: str, text: str, records: dict) -> list[str]:
    where = f"scripts/{folder}/script.json"
    try:
        data = json.loads(text, object_pairs_hook=_no_duplicate_keys)
    except ValueError as exc:
        return [f"{where}: not valid JSON ({exc})"]
    if not isinstance(data, dict):
        return [f"{where}: must be a JSON object"]

    problems: list[str] = []
    for k in sorted(set(data) - SCRIPT_KEYS):
        problems.append(f"{where}: unknown key '{k}'")
    for k in sorted(SCRIPT_KEYS - set(data)):
        problems.append(f"{where}: missing field '{k}'")

    sid = data.get("id")
    if "id" in data:
        if not isinstance(sid, str) or not KEBAB.match(sid):
            problems.append(f"{where}: 'id' must be kebab-case, got {sid!r}")
        elif sid != folder:
            problems.append(f"{where}: 'id' {sid!r} must equal the folder name {folder!r}")
    if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip()):
        problems.append(f"{where}: 'title' must be a non-empty string")
    if "entry" in data:
        entry = data["entry"]
        if not isinstance(entry, str) or not entry:
            problems.append(f"{where}: 'entry' must be a repo-relative path")
        elif entry.startswith("/") or ".." in entry.split("/") or not (root / entry).is_file():
            problems.append(f"{where}: 'entry' {entry!r} is not an existing repo-relative file")

    status = data.get("status")
    if "status" in data and status not in STATUSES:
        problems.append(f"{where}: 'status' {status!r} is not one of {sorted(STATUSES)}")
    if "evidence" in data:
        ids = data["evidence"]
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            problems.append(f"{where}: 'evidence' must be a list of evidence record ids")
        else:
            evidence_mod.check_refs(where, "evidence", ids, folder, records, problems, language="csharp")
            if status == "verified" and not evidence_mod.has_full_pass(ids, records):
                problems.append(f"{where}: status 'verified' needs a passing 'full' evidence record of this "
                                f"script in 'evidence'")

    if "effects" in data and data["effects"] not in EFFECTS:
        problems.append(f"{where}: 'effects' {data['effects']!r} is not one of {sorted(EFFECTS)}")
    for field in ("irreversible", "supportsDryRun", "openTargets"):
        if field in data and not isinstance(data[field], bool):
            problems.append(f"{where}: '{field}' must be true or false")
    if "timeoutMinutes" in data and not (_is_int(data["timeoutMinutes"]) and data["timeoutMinutes"] > 0):
        problems.append(f"{where}: 'timeoutMinutes' must be a positive integer")
    if "params" in data:
        problems.extend(check_params(where, data.get("effects"), data["params"]))
    return problems


def check_csx(folder: str, text: str, open_targets: bool = False) -> list[str]:
    where = f"scripts/{folder}/script.csx"
    problems = []
    forbidden = CSX_FORBIDDEN + (CSX_FORBIDDEN_WITH_OPEN_TARGETS if open_targets else [])
    for n, line in enumerate(text.splitlines(), 1):
        for label, rx in forbidden:
            if rx.search(line):
                problems.append(f"{where}:{n}: forbidden {label}"
                                + (" (openTargets: true; open and close through Kit.Docs)"
                                   if (label, rx) in CSX_FORBIDDEN_WITH_OPEN_TARGETS else ""))
    if "ctx." not in text:
        problems.append(f"{where}: never references 'ctx.' (a script must talk to the host through ctx)")
    return problems


def check_scripts(root: pathlib.Path) -> list[str]:
    base = root / "scripts"
    if not base.is_dir():
        return []
    problems: list[str] = []
    records = evidence_mod.load(root)[1]
    for folder in sorted(p for p in base.iterdir() if p.name not in build_package.SKIP_NAMES):
        rel = f"scripts/{folder.name}"
        if not folder.is_dir():
            problems.append(f"{rel}: only script folders belong in scripts/")
            continue
        names = {p.name for p in folder.iterdir() if p.name not in build_package.SKIP_NAMES}
        for missing in sorted({"script.json", "script.csx"} - names):
            problems.append(f"{rel}: missing {missing}")
        for extra in sorted(names - {"script.json", "script.csx"}):
            problems.append(f"{rel}: unexpected file {extra} (a script folder has exactly script.json and script.csx)")
        open_targets = False
        for name in ("script.json", "script.csx"):
            if name not in names:
                continue
            text, why = textfile.read(folder / name, f"{rel}/{name}")
            if why:
                problems.append(why)
                continue
            if name == "script.json":
                problems.extend(check_script_json(root, folder.name, text, records))
                try:
                    open_targets = json.loads(text).get("openTargets") is True
                except (ValueError, AttributeError):
                    pass
            else:
                problems.extend(check_csx(folder.name, text, open_targets))
    return problems


# --------------------------------------------------------------------------
# skills


def check_frontmatter(rel: str, text: str, name: str) -> list[str]:
    fm = build_manifest.parse_frontmatter(text)
    if fm is None:
        return [f"{rel}: must start with a YAML frontmatter block (--- ... ---)"]
    problems = []
    if fm.get("name") != name:
        problems.append(f"{rel}: frontmatter 'name' must be {name!r}, got {fm.get('name')!r}")
    if not fm.get("description"):
        problems.append(f"{rel}: frontmatter needs a non-empty 'description'")
    return problems


def check_skills(root: pathlib.Path) -> list[str]:
    problems: list[str] = []
    base = root / "skills"
    names = {p.name for p in base.iterdir() if p.is_dir()} if base.is_dir() else set()
    names.add("sw-macro-database")  # the package cannot be built without it
    for name in sorted(names):
        if name == "sw-macro-database":
            rel = f"skills/{name}/SKILL.template.md"
            path = root / rel
            if not path.is_file():
                problems.append(f"{rel} is missing (the release package is generated from it)")
                continue
            text, why = textfile.read(path, rel)
            if why:
                problems.append(why)
                continue
            for ph in build_package.PLACEHOLDERS:
                if "{{" + ph + "}}" not in text:
                    problems.append(f"{rel}: missing placeholder {{{{{ph}}}}}")
            problems.extend(check_frontmatter(rel, text, "sw-macro-database"))
        else:
            rel = f"skills/{name}/SKILL.md"
            path = root / rel
            if not path.is_file():
                problems.append(f"{rel} is missing")
                continue
            text, why = textfile.read(path, rel)
            problems.extend([why] if why else check_frontmatter(rel, text, name))
    return problems


# --------------------------------------------------------------------------
# search


def check_search(zip_path: pathlib.Path, into: pathlib.Path) -> list[str]:
    """Run the packaged lookup.py's self-test on the extracted package."""
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(into)
    skill = into / build_package.SKILL
    spec = importlib.util.spec_from_file_location("packaged_lookup", skill / "lookup.py")
    lookup = importlib.util.module_from_spec(spec)
    dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(lookup)
    finally:
        sys.dont_write_bytecode = dont_write
    if not lookup.has_fts5():
        return [f"search: {lookup.NO_FTS5}"]
    report = io.StringIO()
    try:
        package = lookup.Package(skill)
        conn = package.index()
        try:
            ok = lookup.self_test(package, conn, report)
        finally:
            conn.close()
    except (lookup.PackageError, KeyError, TypeError) as exc:
        return [f"search: the packaged lookup.py cannot read the package: {exc}"]
    if ok:
        return []
    return [f"search: {line}" for line in report.getvalue().splitlines()]


# --------------------------------------------------------------------------
# unit tests


def run_unit_tests(root: pathlib.Path) -> list[str]:
    """tools/tests/, run in-process, so this one command is the whole check."""
    tests = root / "tools" / "tests"
    if not tests.is_dir():
        return []
    suite = unittest.defaultTestLoader.discover(str(tests), top_level_dir=str(root / "tools"))
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    problems = [f"tools/tests: {test.id()} failed:\n{trace}" for test, trace in result.failures + result.errors]
    if result.testsRun == 0:
        problems.append("tools/tests: no tests found")
    return problems


# --------------------------------------------------------------------------


def check_generated(root: pathlib.Path) -> list[str]:
    """The sources' problems, and every generated file that is not what build_manifest.py writes."""
    problems, generated = build_manifest.outputs(root)
    for rel, text in generated.items():
        committed = root / rel
        if not committed.is_file() or committed.read_bytes() != text.encode("utf-8"):
            problems.append(f"{rel} is stale: run python3 tools/build_manifest.py")
    return problems


def validate(root: pathlib.Path, unit_tests: bool = True) -> tuple[list[str], list[str]]:
    """(problems, warnings) for the repo at root."""
    problems: list[str] = []
    warnings: list[str] = []

    problems.extend(check_generated(root))

    problems.extend(check_scripts(root))
    problems.extend(check_skills(root))

    with tempfile.TemporaryDirectory() as tmp:
        try:
            zip_path, warnings = build_package.build(root, "0.0.0-ci", pathlib.Path(tmp))
        except build_package.BuildError as exc:
            problems.append(f"package build failed: {exc}")
        else:
            problems.extend(check_search(zip_path, pathlib.Path(tmp) / "package"))
    try:
        build_package.release_notes(root, build_package.latest_tag(root))
    except (build_package.BuildError, ValueError, KeyError, TypeError) as exc:
        problems.append(f"release notes cannot be written: {exc}")
    if unit_tests:
        problems.extend(run_unit_tests(root))
    # One bad file can be met by several checks; report each problem once.
    return list(dict.fromkeys(problems)), list(dict.fromkeys(warnings))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(ROOT), help="repo root (default: this repo)")
    args = ap.parse_args(argv)

    problems, warnings = validate(pathlib.Path(args.root).resolve())
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if problems:
        print(f"validate: {len(problems)} problem(s):\n", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("validate: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
