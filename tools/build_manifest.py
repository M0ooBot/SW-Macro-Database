#!/usr/bin/env python3
"""Rebuild manifest.json from every entry's frontmatter.

Run from the repo root after adding or changing an entry:

    python3 tools/build_manifest.py

Exits non-zero and prints the problems if any entry is malformed. That is the
one automated quality gate this repo has, so it is deliberately strict.

`collect()` and `render()` do the work without touching the disk, so
tools/validate.py can run the same checks and compare the result with the
committed manifest.json.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

import evidence as evidence_mod
import recipes
from frontmatter import format_value, parse_frontmatter, read_frontmatter  # noqa: F401 (re-exported)

ROOT = pathlib.Path(__file__).resolve().parent.parent

STATUSES = {"verified", "partly-verified", "unverified", "superseded"}

# --------------------------------------------------------------------------
# Entry frontmatter, schema 2: one status for the entry, one for its C# recipe

KEYS_2 = ["schema", "id", "title", "answers", "keywords", "api", "language", "status",
          "verified_on", "majors", "evidence", "recipe_status", "recipe_evidence", "superseded_by"]
# The code an entry shows. C# that SW-Agent runs is only ever the recipe sidecar
# (NN-slug.csx); every other C# is "csharp-standalone".
LANGUAGES = {"python", "csharp-standalone", "vba", "vbscript", "typescript", "shell", "powershell"}
# An entry's own claim. "superseded" is not written: it follows from superseded_by.
CLAIMS = {"verified", "partly-verified", "unverified"}
LIST_FIELDS_2 = {"keywords", "api", "language", "majors", "evidence", "recipe_evidence"}

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Revision majors: 32 is SolidWorks 2024, 34 is 2026.
YEAR_OFFSET = 1992
MAJOR_MIN, MAJOR_MAX = 20, 99


def majors_named(text: str | None) -> set[int]:
    """Revision majors a free-text version names: `34.1.1` gives 34, a year 2024 gives 32.

    A year that is part of a date (2026-11-14) or of a longer number is not a
    version.
    """
    if not text:
        return set()
    found = {int(m.group(1)) for m in re.finditer(r"(?<![\d.])(\d\d)\.\d+(?:\.\d+)?(?![\d])", text)}
    found |= {int(m.group(1)) - YEAR_OFFSET
              for m in re.finditer(r"(?<![\d-])(20\d\d)(?![\d-])", text)}
    return {m for m in found if MAJOR_MIN <= m <= MAJOR_MAX}


def int_list(rel: str, field: str, value, problems: list[str]) -> list[int]:
    out = []
    for v in value or []:
        if not re.fullmatch(r"[0-9]+", v):
            problems.append(f"{rel}: '{field}' item {v!r} is not an integer")
            continue
        out.append(int(v))
    return out


LINK = re.compile(r"\[[^\]]*\]\(([^)#]+?)(?:#[^)]*)?\)")


def check_links(root: pathlib.Path = ROOT) -> list[str]:
    """Every relative markdown link in the repo must resolve.

    Files whose name starts with `_` are skipped: the template's links are
    placeholders by design.
    """
    bad = []
    for md in sorted(root.rglob("*.md")):
        if ".git" in md.parts or md.name.startswith("_"):
            continue
        for m in LINK.finditer(md.read_text(encoding="utf-8")):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (md.parent / target).resolve().exists():
                bad.append(f"{md.relative_to(root).as_posix()}: broken link -> {target}")
    return bad


def check_index(root: pathlib.Path, paths: list[str]) -> list[str]:
    """INDEX.md stays hand-curated, but every entry must be reachable from it."""
    index = root / "INDEX.md"
    if not index.is_file():
        return ["INDEX.md is missing"]
    linked = {(root / m.group(1)).resolve() for m in LINK.finditer(index.read_text(encoding="utf-8"))}
    return [f"{rel}: not linked from INDEX.md" for rel in paths if (root / rel).resolve() not in linked]


def entry_paths(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(p for p in (root / "entries").rglob("*.md") if not p.name.startswith("_"))


def check_entry_2(rel: str, path: pathlib.Path, fm: dict, records: dict, problems: list[str]) -> dict:
    """The schema-2 checks that need nothing but this entry and the evidence records.

    Returns the typed values (majors as integers, the recipe's header) for the
    manifest. Cross-entry checks (superseded_by) are done by collect().
    """
    for k in KEYS_2:
        if k not in fm:
            problems.append(f"{rel}: missing field '{k}'")
    for k in sorted(set(fm) - set(KEYS_2)):
        problems.append(f"{rel}: unknown field '{k}'")
    if fm.get("schema") != "2":
        problems.append(f"{rel}: 'schema' must be 2")
    for field in ("id", "title", "answers"):
        if field in fm and (not isinstance(fm[field], str) or not fm[field].strip()):
            problems.append(f"{rel}: '{field}' must be a non-empty string")
    for field in sorted(LIST_FIELDS_2):
        if field in fm and not isinstance(fm[field], list):
            problems.append(f"{rel}: '{field}' must be an inline list, e.g. [a, b]")
    if isinstance(fm.get("keywords"), list) and not fm["keywords"]:
        problems.append(f"{rel}: 'keywords' must not be empty")

    language = fm.get("language") if isinstance(fm.get("language"), list) else []
    for lang in language:
        if lang == "csharp":
            problems.append(f"{rel}: language 'csharp' is not a value: C# that SW-Agent runs is the "
                            f"recipe sidecar (recipe_status); other C# is 'csharp-standalone'")
        elif lang not in LANGUAGES:
            problems.append(f"{rel}: language {lang!r} is not one of {sorted(LANGUAGES)}")
    if len(set(language)) != len(language):
        problems.append(f"{rel}: 'language' lists a value twice")

    status = fm.get("status")
    if status == "superseded":
        problems.append(f"{rel}: write superseded_by: <entry id> and keep the last status; "
                        f"'superseded' is derived from it")
    elif status not in CLAIMS:
        problems.append(f"{rel}: status {status!r} is not one of {sorted(CLAIMS)}")
    verified_on = fm.get("verified_on")
    if verified_on is not None and not isinstance(verified_on, str):
        problems.append(f"{rel}: 'verified_on' must be text or null")
        verified_on = None

    majors = int_list(rel, "majors", fm.get("majors") if isinstance(fm.get("majors"), list) else [], problems)
    if majors != sorted(set(majors)):
        problems.append(f"{rel}: 'majors' must be ascending with no repeats, e.g. [32, 34]")
    named = majors_named(verified_on)
    for m in majors:
        if not MAJOR_MIN <= m <= MAJOR_MAX:
            problems.append(f"{rel}: major {m} is not a revision major ({MAJOR_MIN}-{MAJOR_MAX}; 34 is SolidWorks 2026)")
        elif m not in named:
            problems.append(f"{rel}: major {m} is not named in verified_on {verified_on!r} "
                            f"(as revision {m}.x or as the year {m + YEAR_OFFSET})")

    entry_id = fm.get("id") if isinstance(fm.get("id"), str) else None
    if entry_id is not None and not KEBAB.match(entry_id):
        problems.append(f"{rel}: 'id' {entry_id!r} must be kebab-case")
    ev_ids = fm.get("evidence") if isinstance(fm.get("evidence"), list) else []
    rec_ids = fm.get("recipe_evidence") if isinstance(fm.get("recipe_evidence"), list) else []
    evidence_mod.check_refs(rel, "evidence", ev_ids, entry_id, records, problems)
    evidence_mod.check_refs(rel, "recipe_evidence", rec_ids, entry_id, records, problems, language="csharp")
    if status == "verified" and not majors and not evidence_mod.has_full_pass(ev_ids, records):
        problems.append(f"{rel}: status 'verified' needs an observation: majors named in verified_on, "
                        f"or a passing 'full' evidence record")

    sidecar = path.with_suffix(".csx")
    recipe_status = fm.get("recipe_status")
    header = None
    if sidecar.is_file():
        if recipe_status not in CLAIMS:
            problems.append(f"{rel}: {sidecar.name} exists, so 'recipe_status' must be one of {sorted(CLAIMS)}")
        header, header_problems = recipes.check(sidecar.read_text(encoding="utf-8"))
        problems.extend(f"{rel[:-3]}.csx: {p}" for p in header_problems)
        if recipe_status == "verified" and not evidence_mod.has_full_pass(rec_ids, records, method="smoke"):
            problems.append(f"{rel}: recipe_status 'verified' needs a passing 'full' evidence record "
                            f"with method 'smoke' in recipe_evidence")
    else:
        if recipe_status is not None:
            problems.append(f"{rel}: 'recipe_status' must be null: there is no {sidecar.name}")
        if rec_ids:
            problems.append(f"{rel}: 'recipe_evidence' must be empty: there is no {sidecar.name}")
    return {"majors": majors, "recipe_header": header, "sidecar": sidecar if sidecar.is_file() else None}


def collect(root: pathlib.Path = ROOT):
    """Check every entry. Returns (problems, manifest); manifest is None if any problem."""
    problems: list[str] = []
    seen_ids: dict[str, str] = {}
    records = []

    paths = entry_paths(root)
    if not paths:
        return ["no entries found"], None

    evidence_problems, evidence_records = evidence_mod.load(root)
    problems.extend(evidence_problems)

    rels = []
    for path in paths:
        rel = path.relative_to(root).as_posix()
        rels.append(rel)
        fm, fm_problems = read_frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            problems.append(f"{rel}: no frontmatter block")
            continue
        problems.extend(f"{rel}: {p}" for p in fm_problems)

        extra = check_entry_2(rel, path, fm, evidence_records, problems)
        status = fm.get("status")

        entry_id = fm.get("id")
        if entry_id:
            if entry_id in seen_ids:
                problems.append(f"{rel}: duplicate id '{entry_id}', also in {seen_ids[entry_id]}")
            seen_ids[entry_id] = rel

        answers = fm.get("answers") or ""
        if answers and not answers.rstrip().endswith("?"):
            problems.append(f"{rel}: 'answers' should be a question ending in '?'")

        records.append({
            "id": entry_id,
            "title": fm.get("title"),
            "path": rel,
            "category": path.parent.name,
            "status": status,
            "verified_on": fm.get("verified_on"),
            "language": fm.get("language", []),
            "api": fm.get("api", []),
            "keywords": fm.get("keywords", []),
            "answers": answers,
        })
        superseded_by = fm.get("superseded_by")
        if superseded_by is not None:
            records[-1]["status"] = "superseded"
        records[-1]["_superseded_by"] = superseded_by

    for r in records:
        target = r.pop("_superseded_by", None)
        if target is not None and (target not in seen_ids or target == r["id"]):
            problems.append(f"{r['path']}: 'superseded_by' {target!r} is not another entry's id")

    problems.extend(evidence_mod.check_subjects(evidence_records, set(seen_ids), script_ids(root)))
    problems.extend(check_index(root, rels))
    problems.extend(check_links(root))
    if problems:
        return problems, None

    by_status: dict[str, int] = {}
    for r in records:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    manifest = {
        "schema": 1,
        "description": (
            "SolidWorks automation entries. Each answers one question. Check "
            "'status' before trusting an entry: verified means it ran against "
            "the named version; unverified means it is well-formed against the "
            "documented API but was never executed."
        ),
        "count": len(records),
        "by_status": dict(sorted(by_status.items())),
        "entries": records,
    }
    return problems, manifest


def script_ids(root: pathlib.Path) -> set[str]:
    base = root / "scripts"
    return {p.name for p in base.iterdir() if p.is_dir()} if base.is_dir() else set()


def render(manifest: dict) -> str:
    """The exact text written to manifest.json."""
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    problems, manifest = collect(ROOT)
    if manifest is None:
        print("manifest not written; fix these first:\n", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    (ROOT / "manifest.json").write_text(render(manifest), encoding="utf-8")
    print(f"manifest.json: {manifest['count']} entries, {manifest['by_status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
