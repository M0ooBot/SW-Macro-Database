"""Gotchas, one file each: gotchas/NNN-slug.md.

    ---
    id: G22
    title: Opening an older file in a newer SolidWorks makes closing it dangerous
    always: false
    members: [CloseDoc]
    languages: [all]
    ---

    The body, free-form markdown, links written from gotchas/ (../entries/...).

The number (NNN, and G<n>) never changes: GOTCHAS §N is cited throughout.
GOTCHAS.md is generated from these files (render_md) and so is gotchas.json
(render_json), which is how SW-Agent and lookup.py read gotcha metadata: they
never parse frontmatter. Files starting with `_` are templates and are skipped.
Python 3 stdlib only.
"""

from __future__ import annotations

import json
import pathlib
import re

import textfile
from frontmatter import read_frontmatter

# GOTCHAS.md's first lines, held here so the generated file has one source.
PREAMBLE = "# Gotchas\n\nThings that cost somebody an afternoon. Read this before writing a new macro.\n"

KEYS = ["id", "title", "always", "members", "languages"]
# How the API is bound, not an entry's language: "all", or the bindings it bites.
LANGUAGES = {"all", "csharp", "pywin32", "late-bound"}
# `Interface.Member` where the gotcha names the interface, else the bare `Member`.
MEMBER = re.compile(r"^(?:I[A-Z][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*$")
FILE = re.compile(r"^(\d{3,})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
LINK = re.compile(r"(\]\()([^)\s]+)(\))")
EXTERNAL = ("http://", "https://", "mailto:")


def anchor(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation dropped, spaces to hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def heading(number: int, title: str) -> str:
    return f"{number}. {title}"


def slug(title: str, limit: int = 48) -> str:
    """A file-name slug from a title: ASCII words, hyphenated, cut at a word end."""
    words = re.sub(r"[^a-z0-9]+", " ", title.lower()).split()
    out = ""
    for w in words:
        nxt = f"{out}-{w}" if out else w
        if len(nxt) > limit and out:
            break
        out = nxt
    return out[:limit] or "gotcha"


def outside_fences(lines: list[str]) -> list[bool]:
    out, fence = [], None
    for line in lines:
        m = re.match(r"^ {0,3}(\x60{3,}|~{3,})", line)
        if fence is None:
            if m:
                fence = m.group(1)
                out.append(False)
            else:
                out.append(True)
        else:
            out.append(False)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and line.strip() == m.group(1):
                fence = None
    return out


def load(root: pathlib.Path):
    """(problems, gotchas) for gotchas/*.md, in number order.

    Each gotcha is {"number", "id", "title", "always", "members", "languages",
    "path", "body"}; body is the file after its frontmatter and the blank line
    that follows it.
    """
    problems: list[str] = []
    gotchas: list[dict] = []
    base = root / "gotchas"
    if not base.is_dir():
        return ["gotchas/ is missing"], []
    for path in sorted(base.iterdir()):
        rel = path.relative_to(root).as_posix()
        if path.name.startswith("_") or path.name == ".DS_Store":
            continue
        m = FILE.match(path.name)
        if not path.is_file() or not m:
            problems.append(f"{rel}: a gotcha file is named NNN-slug.md (three-digit number, kebab-case slug)")
            continue
        text, why = textfile.read(path, rel)
        if why:
            problems.append(why)
            continue
        fm, fm_problems = read_frontmatter(text)
        if fm is None:
            problems.append(f"{rel}: no frontmatter block")
            continue
        problems.extend(f"{rel}: {p}" for p in fm_problems)
        number = int(m.group(1))
        problems.extend(check_fields(rel, number, fm))
        body = text[text.find("\n---\n", 4) + 5:]
        if not body.startswith("\n"):
            problems.append(f"{rel}: leave one blank line after the frontmatter")
        body = body[1:] if body.startswith("\n") else body
        problems.extend(check_body(rel, body))
        gotchas.append({
            "number": number,
            "id": fm.get("id"),
            "title": fm.get("title"),
            "always": fm.get("always"),
            "members": fm.get("members") if isinstance(fm.get("members"), list) else [],
            "languages": fm.get("languages") if isinstance(fm.get("languages"), list) else [],
            "path": rel,
            "body": body,
        })
    gotchas.sort(key=lambda g: g["number"])
    numbers = [g["number"] for g in gotchas]
    if not numbers:
        problems.append("gotchas/ holds no gotchas")
    elif numbers != list(range(1, len(numbers) + 1)):
        dupes = sorted({n for n in numbers if numbers.count(n) > 1})
        problems.append(f"gotcha numbers must run 1..N with no gaps or repeats (repeated: {dupes}); "
                        f"retire a gotcha by turning it into a stub that points to its replacement")
    return problems, gotchas


def check_fields(rel: str, number: int, fm: dict) -> list[str]:
    problems = []
    for k in KEYS:
        if k not in fm:
            problems.append(f"{rel}: missing field '{k}'")
    for k in sorted(set(fm) - set(KEYS)):
        problems.append(f"{rel}: unknown field '{k}'")
    if "id" in fm and fm["id"] != f"G{number}":
        problems.append(f"{rel}: 'id' must be G{number}, from the file name")
    title = fm.get("title")
    if "title" in fm and (not isinstance(title, str) or not title.strip()):
        problems.append(f"{rel}: 'title' must be a non-empty string")
    if "always" in fm and not isinstance(fm["always"], bool):
        problems.append(f"{rel}: 'always' must be true or false, got {fm['always']!r}")
    members = fm.get("members")
    if "members" in fm:
        if not isinstance(members, list):
            problems.append(f"{rel}: 'members' must be an inline list, e.g. [IModelDoc2.SaveAs3, CloseDoc]")
        else:
            for mem in members:
                if not MEMBER.match(mem):
                    problems.append(f"{rel}: member {mem!r} must be Member or Interface.Member")
            if len(set(members)) != len(members):
                problems.append(f"{rel}: 'members' lists a member twice")
    langs = fm.get("languages")
    if "languages" in fm:
        if not isinstance(langs, list) or not langs:
            problems.append(f"{rel}: 'languages' must be a non-empty inline list, e.g. [all]")
        else:
            for lang in langs:
                if lang not in LANGUAGES:
                    problems.append(f"{rel}: language {lang!r} is not one of {sorted(LANGUAGES)}")
            if "all" in langs and len(langs) > 1:
                problems.append(f"{rel}: 'all' stands alone in 'languages'")
            if len(set(langs)) != len(langs):
                problems.append(f"{rel}: 'languages' lists a value twice")
    return problems


def check_body(rel: str, body: str) -> list[str]:
    if not body.strip():
        return [f"{rel}: the body is empty"]
    lines = body.split("\n")
    problems = []
    for n, (line, outside) in enumerate(zip(lines, outside_fences(lines)), 1):
        if outside and re.match(r"^#{1,2}(?: |$)", line):
            problems.append(f"{rel}: body line {n} is a level-1 or level-2 heading; "
                            f"the title is the heading, and GOTCHAS.md puts it there")
    return problems


def root_links(body: str, gotchas: list[dict]) -> str:
    """A gotcha file's links rewritten as GOTCHAS.md (at the repo root) needs them."""
    by_file = {pathlib.PurePosixPath(g["path"]).name: g for g in gotchas}

    def fix(m):
        target = m.group(2)
        if target.startswith(EXTERNAL):
            return m.group(0)
        name, _, _frag = target.partition("#")
        if name in by_file:
            g = by_file[name]
            return m.group(1) + "#" + anchor(heading(g["number"], g["title"])) + m.group(3)
        if target.startswith("../"):
            return m.group(1) + target[3:] + m.group(3)
        return m.group(0)

    return LINK.sub(fix, body)


def file_links(body: str, gotchas: list[dict]) -> str:
    """The inverse of root_links: GOTCHAS.md's links as a gotcha file needs them."""
    by_anchor = {anchor(heading(g["number"], g["title"])): g for g in gotchas}

    def fix(m):
        target = m.group(2)
        if target.startswith(EXTERNAL):
            return m.group(0)
        if target.startswith("#"):
            g = by_anchor.get(target[1:])
            if g is None:
                raise ValueError(f"link to {target} matches no gotcha heading")
            return m.group(1) + pathlib.PurePosixPath(g["path"]).name + m.group(3)
        return m.group(1) + "../" + target + m.group(3)

    return LINK.sub(fix, body)


def render_md(gotchas: list[dict]) -> str:
    """GOTCHAS.md: the preamble, then `## N. Title` and the body of each gotcha."""
    parts = [PREAMBLE]
    for g in gotchas:
        body = root_links(g["body"], gotchas).rstrip("\n") + "\n"
        parts.append(f"\n## {heading(g['number'], g['title'])}\n\n{body}")
    return "".join(parts)


def to_json(gotchas: list[dict]) -> dict:
    return {
        "schema": 1,
        "gotchas": [
            {
                "number": g["number"],
                "id": g["id"],
                "title": g["title"],
                "always": g["always"],
                "members": g["members"],
                "languages": g["languages"],
                "path": g["path"],
            }
            for g in gotchas
        ],
    }


def render_json(gotchas: list[dict]) -> str:
    """gotchas.json: the metadata of every gotcha, in number order."""
    return json.dumps(to_json(gotchas), indent=2, ensure_ascii=False) + "\n"
