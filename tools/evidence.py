"""Evidence records: evidence/<id>.json, one verification each, made after schema 2.

A record says what was run, on which SolidWorks, how, and what was observed:

    {"id": "2026-11-25-sketches-04-cs-32", "subject": "sketches-04-dimensions",
     "language": "csharp", "swRevision": "32.5.0", "major": 32, "date": "2026-11-25",
     "method": "smoke", "result": "pass", "scope": "full",
     "observed": "Closed profile of 4 lines on Front Plane; sketch fully defined."}

Entries list their records in `evidence` (and a C# recipe's in `recipe_evidence`);
a script lists its own in script.json. A subject's effective majors are its own
plus the majors of its passing records. Files starting with `_` are templates.
Python 3 stdlib only.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import re

KEYS = ["id", "subject", "language", "swRevision", "major", "date", "method", "result", "scope", "observed"]
LANGUAGES = {"csharp", "python", "csharp-standalone", "vba", "vbscript", "typescript", "shell", "powershell"}
METHODS = {"smoke", "contribution", "probe", "manual"}
RESULTS = {"pass", "fail"}
SCOPES = {"full", "partial"}
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REVISION = re.compile(r"^(\d+)\.\d+\.\d+$")

# "observed" is published: it must not carry a machine's paths, a user name or
# the user's file names.
PRIVATE = [
    ("a Windows path", re.compile(r"(?i)(?<![A-Za-z])[A-Z]:[\\/]")),
    ("a UNC or WSL path", re.compile(r"(?i)\\\\|/mnt/[a-z]/|/home/|/Users/|wsl\.localhost|wsl\$")),
    ("a file name", re.compile(r"(?i)\b[\w~-]+\.(?:sldprt|sldasm|slddrw|step|stp|igs|iges|x_t|x_b|dwg|dxf|pdf|swp)\b")),
]


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def check_record(rel: str, stem: str, data) -> list[str]:
    if not isinstance(data, dict):
        return [f"{rel}: must be a JSON object"]
    problems = []
    for k in KEYS:
        if k not in data:
            problems.append(f"{rel}: missing field '{k}'")
    for k in sorted(set(data) - set(KEYS)):
        problems.append(f"{rel}: unknown field '{k}'")
    rid = data.get("id")
    if not isinstance(rid, str) or not ID.match(rid):
        problems.append(f"{rel}: 'id' must be kebab-case, got {rid!r}")
    elif rid != stem:
        problems.append(f"{rel}: 'id' {rid!r} must equal the file name {stem!r}")
    if not isinstance(data.get("subject"), str) or not data.get("subject"):
        problems.append(f"{rel}: 'subject' must be an entry id or a script id")
    if data.get("language") not in LANGUAGES:
        problems.append(f"{rel}: 'language' {data.get('language')!r} is not one of {sorted(LANGUAGES)}")
    major = data.get("major")
    if not _int(major) or not 20 <= major <= 99:
        problems.append(f"{rel}: 'major' must be a revision major (32 is SolidWorks 2024), got {major!r}")
    rev = data.get("swRevision")
    if rev is not None:
        m = REVISION.match(rev) if isinstance(rev, str) else None
        if not m:
            problems.append(f"{rel}: 'swRevision' must look like 34.1.1, or be null, got {rev!r}")
        elif _int(major) and int(m.group(1)) != major:
            problems.append(f"{rel}: 'swRevision' {rev} is not major {major}")
    date = data.get("date")
    try:
        ok = isinstance(date, str) and datetime.date.fromisoformat(date).isoformat() == date
    except ValueError:
        ok = False
    if not ok:
        problems.append(f"{rel}: 'date' must be YYYY-MM-DD, got {date!r}")
    for field, allowed in (("method", METHODS), ("result", RESULTS), ("scope", SCOPES)):
        if data.get(field) not in allowed:
            problems.append(f"{rel}: '{field}' {data.get(field)!r} is not one of {sorted(allowed)}")
    observed = data.get("observed")
    if not isinstance(observed, str) or not observed.strip():
        problems.append(f"{rel}: 'observed' must say what was observed")
    else:
        for label, rx in PRIVATE:
            if rx.search(observed):
                problems.append(f"{rel}: 'observed' holds {label}; describe it instead")
    return problems


def load(root: pathlib.Path):
    """(problems, {id: record}) for every evidence/*.json that is not a template."""
    problems: list[str] = []
    records: dict[str, dict] = {}
    base = root / "evidence"
    if not base.is_dir():
        return problems, records
    for path in sorted(base.iterdir()):
        rel = path.relative_to(root).as_posix()
        if path.name.startswith("_") or path.name in (".DS_Store",):
            continue
        if not path.is_file() or path.suffix != ".json":
            problems.append(f"{rel}: only <id>.json records belong in evidence/")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            problems.append(f"{rel}: not valid JSON ({exc})")
            continue
        found = check_record(rel, path.stem, data)
        problems.extend(found)
        if not found:
            records[data["id"]] = data
    return problems, records


def check_refs(rel: str, field: str, ids, subject, records: dict, problems: list[str], language=None) -> None:
    """Every id in a subject's list names a record about that subject."""
    if len(set(ids)) != len(ids):
        problems.append(f"{rel}: '{field}' lists a record twice")
    for rid in ids:
        rec = records.get(rid)
        if rec is None:
            problems.append(f"{rel}: '{field}' names {rid!r}, which is not a valid evidence/{rid}.json")
            continue
        if rec["subject"] != subject:
            problems.append(f"{rel}: '{field}' names {rid!r}, whose subject is {rec['subject']!r}")
        if language is not None and rec["language"] != language:
            problems.append(f"{rel}: '{field}' names {rid!r}, whose language is {rec['language']!r}, not {language!r}")


def has_full_pass(ids, records: dict, method=None) -> bool:
    return any(
        rid in records and records[rid]["result"] == "pass" and records[rid]["scope"] == "full"
        and (method is None or records[rid]["method"] == method)
        for rid in ids
    )


def passing_majors(ids, records: dict) -> set[int]:
    return {records[rid]["major"] for rid in ids if rid in records and records[rid]["result"] == "pass"}


def check_subjects(records: dict, entry_ids: set[str], script_ids: set[str]) -> list[str]:
    return [
        f"evidence/{rid}.json: 'subject' {rec['subject']!r} is neither an entry id nor a script id"
        for rid, rec in sorted(records.items())
        if rec["subject"] not in entry_ids and rec["subject"] not in script_ids
    ]
