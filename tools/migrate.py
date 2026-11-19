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

COMMANDS = {"entries": migrate_entries}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in COMMANDS:
        print(f"usage: migrate.py {{{'|'.join(COMMANDS)}}}", file=sys.stderr)
        return 2
    return COMMANDS[argv[0]]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
