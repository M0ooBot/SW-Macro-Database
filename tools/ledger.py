"""The API ledger as data: api-ledger.json, and API-LEDGER.md generated from it.

One row per call form, as the ledger has always been written:

    {"section": "IModelDocExtension", "interface": "IModelDocExtension",
     "members": ["IModelDocExtension.SelectByID2"], "form": "`SelectByID2(name, \"PLANE\", …)`",
     "purpose": "…", "on": null, "status": "verified",
     "note": "Verified, SW 2026 (34.0.0), dev runs 2026-09-15",
     "provenance": "dev runs 2026-09-15", "languages": [], "majors": [34], "evidence": []}

- `status` is the claim: verified, partly-verified, unverified, fails (observed not to
  work) or absent (observed not to exist). `majors` are where it was observed.
- `note` is the Status cell's own wording whenever it says more than the status
  (a version, a run, a condition); API-LEDGER.md shows the note in that cell, or
  the plain status when there is none. One note is special: "no version
  recorded" marks a row whose source says "Verified" and nothing more; the cell
  shows "Verified" and SW-Agent shows the note.
- `provenance` is the run the cell names ("dev runs 2026-09-15"); the preamble
  says what each run was.
- `members`: every API member the Member cell names, qualified with an interface
  where the cell or a one-interface section heading gives one.

Python 3 stdlib only.
"""

from __future__ import annotations

import json
import pathlib
import re

TITLE = "# API ledger\n\n"
STATUSES = ["verified", "partly-verified", "unverified", "fails", "absent"]
LABELS = {"verified": "Verified", "partly-verified": "Partly verified", "unverified": "Unverified"}
NO_VERSION = "no version recorded"
LANGUAGES = {"csharp", "pywin32", "late-bound"}
TOP_KEYS = ["schema", "preamble", "sections", "rows"]
SECTION_KEYS = ["title", "note"]
ROW_KEYS = ["section", "interface", "members", "form", "purpose", "on", "status", "note",
            "provenance", "languages", "majors", "evidence"]
INTERFACE = re.compile(r"^I[A-Z][A-Za-z0-9_]*$")
MEMBER = re.compile(r"^(?:I[A-Z][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*$")


def _no_duplicate_keys(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError(f"duplicate key {k!r}")
        obj[k] = v
    return obj


def load(root: pathlib.Path):
    """(problems, ledger or None) from api-ledger.json, shape not yet checked."""
    path = root / "api-ledger.json"
    if not path.is_file():
        return ["api-ledger.json is missing"], None
    try:
        return [], json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    except (ValueError, UnicodeDecodeError) as exc:
        return [f"api-ledger.json: not valid JSON ({exc})"], None


def _one_line(v) -> bool:
    return isinstance(v, str) and v.strip() == v and v != "" and "\n" not in v


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def check(ledger, evidence_ids: set[str]) -> list[str]:
    """Every rule the ledger's shape and claims must meet."""
    w = "api-ledger.json"
    if not isinstance(ledger, dict):
        return [f"{w}: must be a JSON object"]
    problems = [f"{w}: missing key '{k}'" for k in TOP_KEYS if k not in ledger]
    problems += [f"{w}: unknown key '{k}'" for k in sorted(set(ledger) - set(TOP_KEYS))]
    if ledger.get("schema") != 1:
        problems.append(f"{w}: 'schema' must be 1")
    preamble = ledger.get("preamble")
    if not isinstance(preamble, str) or not preamble.endswith("\n") or preamble.endswith("\n\n"):
        problems.append(f"{w}: 'preamble' must be text ending in exactly one newline")
    sections = ledger.get("sections")
    titles: list[str] = []
    if not isinstance(sections, list):
        problems.append(f"{w}: 'sections' must be a list")
        sections = []
    for i, s in enumerate(sections):
        where = f"{w}: sections[{i}]"
        if not isinstance(s, dict) or set(s) != set(SECTION_KEYS):
            problems.append(f"{where}: must be an object with exactly {SECTION_KEYS}")
            continue
        if not _one_line(s["title"]):
            problems.append(f"{where}: 'title' must be one line of text")
        elif s["title"] in titles:
            problems.append(f"{where}: title {s['title']!r} appears twice")
        titles.append(s["title"])
        note = s["note"]
        if note is not None and (not isinstance(note, str) or note != note.strip() or not note):
            problems.append(f"{where}: 'note' must be null or text with no leading or trailing blank")
    rows = ledger.get("rows")
    if not isinstance(rows, list):
        return problems + [f"{w}: 'rows' must be a list"]
    has_on: dict[str, set[bool]] = {}
    for i, r in enumerate(rows):
        where = f"{w}: rows[{i}]"
        if not isinstance(r, dict):
            problems.append(f"{where}: must be an object")
            continue
        problems += [f"{where}: missing key '{k}'" for k in ROW_KEYS if k not in r]
        problems += [f"{where}: unknown key '{k}'" for k in sorted(set(r) - set(ROW_KEYS))]
        if any(k not in r for k in ROW_KEYS):
            continue
        where = f"{w}: rows[{i}] ({r['form']!r})" if isinstance(r["form"], str) else where
        if r["section"] not in titles:
            problems.append(f"{where}: 'section' {r['section']!r} is not a section title")
        if r["interface"] is not None and not (isinstance(r["interface"], str) and INTERFACE.match(r["interface"])):
            problems.append(f"{where}: 'interface' must be null or an interface name such as IModelDoc2")
        members = r["members"]
        if not isinstance(members, list) or not all(isinstance(m, str) and MEMBER.match(m) for m in members):
            problems.append(f"{where}: 'members' must be a list of Member or Interface.Member")
        elif len(set(members)) != len(members):
            problems.append(f"{where}: 'members' lists a member twice")
        for field in ("form", "purpose"):
            if not _one_line(r[field]):
                problems.append(f"{where}: '{field}' must be one line of text")
        if r["on"] is not None and not _one_line(r["on"]):
            problems.append(f"{where}: 'on' must be null or one line of text")
        has_on.setdefault(r["section"], set()).add(r["on"] is not None)
        status = r["status"]
        if status not in STATUSES:
            problems.append(f"{where}: 'status' {status!r} is not one of {STATUSES}")
        note = r["note"]
        if note is not None and not _one_line(note):
            problems.append(f"{where}: 'note' must be null or one line of text")
        if status in ("fails", "absent") and note is None:
            problems.append(f"{where}: a '{status}' row needs its wording in 'note'")
        if r["provenance"] is not None and not _one_line(r["provenance"]):
            problems.append(f"{where}: 'provenance' must be null or one line of text")
        langs = r["languages"]
        if not isinstance(langs, list) or not all(l in LANGUAGES for l in langs) or len(set(langs)) != len(langs):
            problems.append(f"{where}: 'languages' must list distinct values of {sorted(LANGUAGES)}")
        majors = r["majors"]
        if not isinstance(majors, list) or not all(_int(m) and 20 <= m <= 99 for m in majors):
            problems.append(f"{where}: 'majors' must list revision majors (32 is SolidWorks 2024)")
            majors = []
        elif majors != sorted(set(majors)):
            problems.append(f"{where}: 'majors' must be ascending with no repeats")
        ev = r["evidence"]
        if not isinstance(ev, list) or not all(isinstance(e, str) for e in ev):
            problems.append(f"{where}: 'evidence' must be a list of evidence ids")
            ev = []
        for e in ev:
            if e not in evidence_ids:
                problems.append(f"{where}: evidence {e!r} is not a valid evidence/{e}.json")
        if note == NO_VERSION and (status != "verified" or majors):
            problems.append(f"{where}: the note {NO_VERSION!r} is only for a 'verified' row with no majors")
        if status == "verified" and not majors and not ev and note != NO_VERSION:
            problems.append(f"{where}: 'verified' needs majors, evidence, or the note {NO_VERSION!r}")
    for title, flags in has_on.items():
        if len(flags) > 1:
            problems.append(f"{w}: section {title!r}: give 'on' in every row or in none")
    return problems


def status_cell(row: dict) -> str:
    note = row["note"]
    return LABELS[row["status"]] if note is None or note == NO_VERSION else note


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_md(ledger: dict) -> str:
    """API-LEDGER.md: the preamble, then each section's note and table."""
    out = [TITLE, ledger["preamble"]]
    for s in ledger["sections"]:
        out.append(f"\n## {s['title']}\n")
        if s["note"] is not None:
            out.append(f"\n{s['note']}\n")
        rows = [r for r in ledger["rows"] if r["section"] == s["title"]]
        if not rows:
            continue
        with_on = rows[0]["on"] is not None
        header = ["Member", "On", "Purpose", "Status"] if with_on else ["Member", "Purpose", "Status"]
        out.append("\n| " + " | ".join(header) + " |\n|" + "---|" * len(header) + "\n")
        for r in rows:
            cells = [r["form"]] + ([r["on"]] if with_on else []) + [r["purpose"], status_cell(r)]
            out.append("| " + " | ".join(_cell(c) for c in cells) + " |\n")
    return "".join(out)


def render_json(ledger: dict) -> str:
    return json.dumps(ledger, indent=2, ensure_ascii=False) + "\n"
