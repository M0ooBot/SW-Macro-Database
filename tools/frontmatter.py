"""The one reader of frontmatter in this repo.

Entries (entries/**/NN-slug.md), gotchas (gotchas/NNN-slug.md) and skills
(skills/*/SKILL.md) start with a block between two `---` lines. Everything that
reads that block goes through read_frontmatter(); SW-Agent and lookup.py never
do: they read manifest.json and gotchas.json, which tools/build_manifest.py
writes from it. Python 3 stdlib only.
"""

from __future__ import annotations

import re


def read_frontmatter(text: str):
    """(fields, problems) for the block between the first two `---` lines.

    fields is None when there is no block. A deliberately small reader: one
    `key: value` per line; the value is `null` (or `~` or nothing),
    `true`/`false`, an inline list `[a, b]`, a quoted string, or the rest of the
    line. A line it cannot read, or a key given twice, is a problem rather than
    something skipped: anything fancier is a sign the frontmatter is doing too
    much.
    """
    if not text.startswith("---\n"):
        return None, []
    end = text.find("\n---\n", 4)
    if end < 0:
        return None, []
    out: dict = {}
    problems: list[str] = []
    for n, line in enumerate(text[4:end].split("\n"), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not m:
            problems.append(f"frontmatter line {n} cannot be read: {line!r}")
            continue
        key, raw = m.group(1), m.group(2).strip()
        if key in out:
            problems.append(f"frontmatter key '{key}' appears twice")
            continue
        out[key] = parse_value(raw)
    return out, problems


def parse_value(raw: str):
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [v.strip().strip('"\'') for v in inner.split(",") if v.strip()]
    if raw in ("null", "~", ""):
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        return re.sub(r'\\(["\\])', r"\1", raw[1:-1])
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    return raw.strip('"\'')


def parse_frontmatter(text: str):
    """The frontmatter as a dict, or None when there is none (problems ignored)."""
    return read_frontmatter(text)[0]
