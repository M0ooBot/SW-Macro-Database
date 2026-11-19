#!/usr/bin/env python3
"""Build the release package: dist/sw-macro-database-<version>.zip.

    python3 tools/build_package.py --version 2.0.0 --out dist/
    python3 tools/build_package.py --version 2.0.0 --out dist/ --notes-from v1.0.0

The package holds two skills plus the prebuilt scripts:

    package.json                                  schema 2: every file's hash and size, the scripts, minKit
    skills/sw-macro-database/SKILL.md             rendered: version, always-list, scripts, index
    skills/sw-macro-database/search.sql           the search tables and ranking queries
    skills/sw-macro-database/search-tests.json    match-text vectors and test questions
    skills/sw-macro-database/lookup.py            stand-alone search (Python with FTS5)
    skills/sw-macro-database/manifest.json, gotchas.json, api-ledger.json
    skills/sw-macro-database/GOTCHAS.md, API-LEDGER.md, INDEX.md, CONTRIBUTING.md
    skills/sw-macro-database/entries/, gotchas/, evidence/, code/
    skills/sw-macro-contribute/SKILL.md, CONTRIBUTING.md, _TEMPLATE.md, _GOTCHA_TEMPLATE.md
    scripts/<id>/script.json, script.csx

The zip is deterministic: sorted entries, a fixed timestamp, fixed modes.
Building the same commit twice gives byte-identical output, so the sha256
values in package.json can be trusted. Every path keeps the path rule SW-Agent
enforces when it installs a package (check_path), so no release can be built
that the bridge would refuse.

`--notes-from <ref>` also writes dist/release-notes.md: what changed in the
format, the scripts and the entries since that tag. Omit it, or name a ref
that does not exist, and everything is listed as new (a first release).

Python 3 stdlib only. Fails (non-zero, message on stderr) rather than producing
a package with a broken template, a broken link inside entries/ or code/, or a
path the bridge would refuse.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import posixpath
import re
import subprocess
import sys
import urllib.parse
import zipfile

import build_manifest
import evidence as evidence_mod

ROOT = pathlib.Path(__file__).resolve().parent.parent

SKILL = "skills/sw-macro-database"
CONTRIBUTE = "skills/sw-macro-contribute"
PLACEHOLDERS = ("VERSION", "ALWAYS", "SCRIPTS", "INDEX")
SKILL_FILES = ("search.sql", "search-tests.json", "lookup.py")
SKIP_NAMES = {".DS_Store", "__pycache__"}
SKIP_SUFFIXES = {".pyc"}
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
ASSET = "sw-macro-database-{version}.zip"
# SemVer 2.0, no leading v.
VERSION_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

# The path rule (the bridge refuses a package that breaks it).
SEGMENT = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]*$")
DEVICES = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
MAX_PATH, MAX_SEGMENTS = 150, 12


class BuildError(Exception):
    """The package cannot be built; the message says why."""


def check_path(path: str) -> str | None:
    """Why a package path breaks the path rule, or None when it keeps it."""
    if len(path) > MAX_PATH:
        return f"longer than {MAX_PATH} characters"
    segments = path.split("/")
    if len(segments) > MAX_SEGMENTS:
        return f"more than {MAX_SEGMENTS} segments"
    for s in segments:
        if not SEGMENT.match(s):
            return f"segment {s!r} is not [A-Za-z0-9_-][A-Za-z0-9._-]*"
        if s.endswith("."):
            return f"segment {s!r} ends in '.'"
        if s.split(".")[0].upper() in DEVICES:
            return f"segment {s!r} is a Windows device name"
    return None


def _skipped(path: pathlib.Path) -> bool:
    return (
        path.name in SKIP_NAMES
        or path.suffix in SKIP_SUFFIXES
        or any(part in SKIP_NAMES for part in path.parts)
    )


def _read(root: pathlib.Path, rel: str) -> bytes:
    path = root / rel
    if not path.is_file():
        raise BuildError(f"{rel} is missing")
    return path.read_bytes()


def _tree(root: pathlib.Path, rel_dir: str, dest: str) -> dict[str, bytes]:
    """Every file under root/rel_dir, keyed by its path inside the package."""
    base = root / rel_dir
    out: dict[str, bytes] = {}
    if not base.is_dir():
        return out
    for path in sorted(base.rglob("*")):
        if not path.is_file() or _skipped(path.relative_to(base)):
            continue
        out[f"{dest}/{path.relative_to(base).as_posix()}"] = path.read_bytes()
    return out


def read_kit_version(root: pathlib.Path) -> str:
    text = _read(root, "kit.version").decode("utf-8").strip()
    if not VERSION_RE.match(text):
        raise BuildError(f"kit.version {text!r} is not a SemVer version such as 0.1.0")
    return text


# --------------------------------------------------------------------------
# scripts


def load_scripts(root: pathlib.Path) -> dict[str, dict]:
    """{id: {"meta": script.json dict, "sha256": ..., "json": bytes, "csx": bytes, "majors": [...]}}.

    Reads only; the shape of script.json is tools/validate.py's job. A folder
    that cannot even be read raises BuildError.
    """
    out: dict[str, dict] = {}
    base = root / "scripts"
    if not base.is_dir():
        return out
    records = evidence_mod.load(root)[1]
    for folder in sorted(p for p in base.iterdir() if p.is_dir() and p.name not in SKIP_NAMES):
        raw_json = _read(root, f"scripts/{folder.name}/script.json")
        raw_csx = _read(root, f"scripts/{folder.name}/script.csx")
        try:
            meta = json.loads(raw_json.decode("utf-8"))
        except ValueError as exc:
            raise BuildError(f"scripts/{folder.name}/script.json: not valid JSON ({exc})")
        if not isinstance(meta, dict):
            raise BuildError(f"scripts/{folder.name}/script.json: must be a JSON object")
        ids = meta.get("evidence") if isinstance(meta.get("evidence"), list) else []
        out[folder.name] = {
            "meta": meta,
            "json": raw_json,
            "csx": raw_csx,
            # The two files, back to back, are what a consumer must reproduce.
            "sha256": hashlib.sha256(raw_json + raw_csx).hexdigest(),
            "majors": sorted(evidence_mod.passing_majors(ids, records)),
        }
    return out


# --------------------------------------------------------------------------
# SKILL.md generation


def render_index(manifest: dict) -> str:
    """One line per entry, grouped by category, in manifest order."""
    groups: dict[str, list[dict]] = {}
    for e in manifest["entries"]:
        groups.setdefault(e["category"], []).append(e)
    blocks = []
    for category, entries in groups.items():
        lines = [f"### {category}", ""]
        for e in entries:
            recipe = f" · C# recipe **{e['recipe']['status']}**" if e["recipe"] else ""
            lines.append(f"- `{e['path']}` · **{e['status']}**{recipe} · {e['answers']}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_scripts(scripts: dict[str, dict]) -> str:
    if not scripts:
        return "No prebuilt scripts in this release."
    lines = []
    for sid in sorted(scripts):
        m = scripts[sid]["meta"]
        irreversible = ", irreversible" if m.get("irreversible") else ""
        majors = scripts[sid]["majors"]
        ran = f" (majors {', '.join(str(x) for x in majors)})" if majors else ""
        lines.append(
            f"- `{sid}` · {m.get('effects')}{irreversible} · **{m.get('status')}**{ran}"
            f" · {m.get('title')} · entry `{m.get('entry')}`"
        )
    return "\n".join(lines)


def render_always(gotchas: dict) -> str:
    """The always-list: one "**G<n>** <title>" line per gotcha, linking to its file."""
    rows = [g for g in gotchas["gotchas"] if g["always"]]
    if not rows:
        return "No gotcha is on the always-list in this release."
    return "\n".join(f"- **G{g['number']}** [{g['title']}]({g['path']})" for g in rows)


def render_skill(template: str, version: str, manifest: dict, gotchas: dict, scripts: dict[str, dict]) -> str:
    """Fill the placeholders in one pass, so substituted text is never rescanned."""
    values = {
        "VERSION": version,
        "ALWAYS": render_always(gotchas),
        "SCRIPTS": render_scripts(scripts),
        "INDEX": render_index(manifest),
    }
    missing = [p for p in PLACEHOLDERS if "{{" + p + "}}" not in template]
    if missing:
        raise BuildError(
            f"{SKILL}/SKILL.template.md lacks placeholder(s): "
            + ", ".join("{{" + p + "}}" for p in missing)
        )
    return re.sub(r"\{\{(" + "|".join(PLACEHOLDERS) + r")\}\}", lambda m: values[m.group(1)], template)


# --------------------------------------------------------------------------
# link check


def check_package_links(files: dict[str, bytes]) -> tuple[list[str], list[str]]:
    """Relative markdown links inside the packaged skills/sw-macro-database/**.

    Returns (errors, warnings). Inside entries/, gotchas/ and code/ an
    unresolved link is an error: those folders are meant to be self-contained.
    Elsewhere (GOTCHAS, API-LEDGER, INDEX) a link to a repo-root file that is
    not packaged is only a warning. Content is never rewritten.
    """
    errors: list[str] = []
    warnings: list[str] = []
    paths = set(files)
    dirs = {posixpath.dirname(p) for p in paths}
    for p in list(dirs):
        while p:
            p = posixpath.dirname(p)
            dirs.add(p)
    for path in sorted(files):
        if not (path.startswith(SKILL + "/") and path.endswith(".md")):
            continue
        # As in build_manifest.check_links: files starting with `_` are templates,
        # and their links are placeholders by design.
        if posixpath.basename(path).startswith("_"):
            continue
        rel = path[len(SKILL) + 1:]
        strict = rel.startswith(("entries/", "gotchas/", "code/"))
        for m in build_manifest.LINK.finditer(files[path].decode("utf-8")):
            target = urllib.parse.unquote(m.group(1).strip())
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
            inside = resolved.startswith(SKILL + "/") or resolved == SKILL
            if inside and (resolved in paths or resolved in dirs):
                continue
            msg = f"{path}: link does not resolve inside the package -> {target}"
            (errors if strict else warnings).append(msg)
    return errors, warnings


# --------------------------------------------------------------------------
# build


def git_bytes(root: pathlib.Path, *args: str) -> bytes | None:
    """Raw stdout of a git command run in root, or None if it fails.

    Bytes, not text: the script sha256 is over exact bytes, so no newline
    translation is allowed on the way in.
    """
    try:
        res = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return res.stdout


def git(root: pathlib.Path, *args: str) -> str | None:
    out = git_bytes(root, *args)
    return None if out is None else out.decode("utf-8", errors="replace")


def head_commit(root: pathlib.Path) -> str:
    if not (root / ".git").exists():
        return "unknown"
    out = git(root, "rev-parse", "HEAD")
    return out.strip() if out and out.strip() else "unknown"


def assemble(root: pathlib.Path, version: str) -> tuple[dict[str, bytes], list[str]]:
    """Every file in the package, keyed by path, plus link warnings. No disk writes."""
    if not VERSION_RE.match(version):
        raise BuildError(f"version {version!r} must be SemVer, such as 2.0.0 (no leading 'v')")
    min_kit = read_kit_version(root)

    manifest_bytes = _read(root, "manifest.json")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    gotchas_bytes = _read(root, "gotchas.json")
    gotchas = json.loads(gotchas_bytes.decode("utf-8"))
    if manifest.get("schema") != 2:
        raise BuildError("manifest.json is not schema 2: run python3 tools/build_manifest.py")
    scripts = load_scripts(root)
    template = _read(root, f"{SKILL}/SKILL.template.md").decode("utf-8")

    files: dict[str, bytes] = {
        f"{SKILL}/SKILL.md": render_skill(template, version, manifest, gotchas, scripts).encode("utf-8"),
        f"{SKILL}/manifest.json": manifest_bytes,
        f"{SKILL}/gotchas.json": gotchas_bytes,
        f"{SKILL}/GOTCHAS.md": _read(root, "GOTCHAS.md"),
        f"{SKILL}/api-ledger.json": _read(root, "api-ledger.json"),
        f"{SKILL}/API-LEDGER.md": _read(root, "API-LEDGER.md"),
        f"{SKILL}/INDEX.md": _read(root, "INDEX.md"),
        # Entries link to ../../CONTRIBUTING.md (the authoring rules); packaging a
        # copy at the skill root keeps those links resolving without rewriting them.
        f"{SKILL}/CONTRIBUTING.md": _read(root, "CONTRIBUTING.md"),
        f"{CONTRIBUTE}/SKILL.md": _read(root, f"{CONTRIBUTE}/SKILL.md"),
        f"{CONTRIBUTE}/CONTRIBUTING.md": _read(root, "CONTRIBUTING.md"),
        f"{CONTRIBUTE}/_TEMPLATE.md": _read(root, "entries/_TEMPLATE.md"),
        f"{CONTRIBUTE}/_GOTCHA_TEMPLATE.md": _read(root, "gotchas/_TEMPLATE.md"),
    }
    for name in SKILL_FILES:
        files[f"{SKILL}/{name}"] = _read(root, f"{SKILL}/{name}")
    for folder in ("entries", "gotchas", "evidence", "code"):
        files.update(_tree(root, folder, f"{SKILL}/{folder}"))
    for sid, s in scripts.items():
        files[f"scripts/{sid}/script.json"] = s["json"]
        files[f"scripts/{sid}/script.csx"] = s["csx"]

    errors, warnings = check_package_links(files)
    seen: dict[str, str] = {}
    for p in sorted(files) + ["package.json"]:
        why = check_path(p)
        if why:
            errors.append(f"{p}: breaks the package path rule: {why}")
        if p.lower() in seen:
            errors.append(f"{p}: differs from {seen[p.lower()]} only in case")
        seen[p.lower()] = p
    if errors:
        raise BuildError("the package would be refused:\n  " + "\n  ".join(errors))

    package_json = {
        "schema": 2,
        "version": version,
        "builtFrom": head_commit(root),
        "minKit": min_kit,
        "files": [
            {"path": p, "sha256": hashlib.sha256(files[p]).hexdigest(), "size": len(files[p])}
            for p in sorted(files)
        ],
        "scripts": [
            {
                "id": sid,
                "sha256": scripts[sid]["sha256"],
                "effects": scripts[sid]["meta"].get("effects"),
                "irreversible": scripts[sid]["meta"].get("irreversible"),
                "status": scripts[sid]["meta"].get("status"),
                "majors": scripts[sid]["majors"],
            }
            for sid in sorted(scripts)
        ],
    }
    files["package.json"] = (json.dumps(package_json, indent=2) + "\n").encode("utf-8")
    return files, warnings


def write_zip(files: dict[str, bytes], dest: pathlib.Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(files):
            info = zipfile.ZipInfo(path, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # unix, whatever the build machine is
            info.external_attr = 0o644 << 16
            zf.writestr(info, files[path])
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(buf.getvalue())


def build(root: pathlib.Path, version: str, out_dir: pathlib.Path) -> tuple[pathlib.Path, list[str]]:
    """Build the zip. Returns (zip path, warnings); raises BuildError on failure."""
    files, warnings = assemble(root, version)
    dest = out_dir / ASSET.format(version=version)
    write_zip(files, dest)
    return dest, warnings


# --------------------------------------------------------------------------
# release notes

# What a reader of the old format needs to know, per (old schema, new schema).
FORMAT_CHANGES = {
    (1, 2): [
        "This release changes the package format; a reader of the old one cannot read it.",
        "",
        "- **Entries:** frontmatter and `manifest.json` schema 2. One `status` per entry, as before,",
        "  plus `majors` (the SolidWorks revision majors it ran on, 32 = 2024, 34 = 2026), `evidence`",
        "  records, and a separate status for an entry's C# recipe (`recipe`; none yet). The",
        "  `language` value `csharp` is now `csharp-standalone`; `any` and `n/a` are now empty lists.",
        "- **Gotchas:** one file each under `gotchas/`, numbers kept, with `gotchas.json` (the",
        "  always-list, member and binding tags); `GOTCHAS.md` is generated from them.",
        "- **API ledger:** `api-ledger.json`, one row per call form with a status from a fixed set;",
        "  `API-LEDGER.md` is generated from it.",
        "- **Scripts:** `script.json` lists evidence record ids and `openTargets`; `edits-open-document`",
        "  is a new effect. `package.json` (schema 2) gives each script's effects, irreversibility,",
        "  status and majors, every file's size, and `minKit`, the oldest SW-Agent `Kit` it needs.",
        "- **Search:** `search.sql`, `search-tests.json` and `lookup.py` in the `sw-macro-database`",
        "  skill folder; `lookup.py` searches without SW-Agent (Python with SQLite FTS5).",
        "- **Asset:** `sw-macro-database-<version>.zip` (was `swfm-skills-<version>.zip`).",
    ],
}


def _at_ref(root: pathlib.Path, ref: str | None):
    """(manifest dict, {script id: (meta, sha)}) at a git ref; (None, None) if no such ref."""
    if not ref:
        return None, None
    raw = git_bytes(root, "show", f"{ref}:manifest.json")
    if raw is None:
        return None, None
    manifest = json.loads(raw)
    scripts: dict[str, tuple[dict, str]] = {}
    listing = git(root, "ls-tree", "-r", "--name-only", ref, "scripts/") or ""
    ids = sorted({p.split("/")[1] for p in listing.splitlines() if p.count("/") >= 2})
    for sid in ids:
        j = git_bytes(root, "show", f"{ref}:scripts/{sid}/script.json")
        c = git_bytes(root, "show", f"{ref}:scripts/{sid}/script.csx")
        if j is None or c is None:
            continue
        try:
            meta = json.loads(j)
        except ValueError:
            meta = {}
        scripts[sid] = (meta, hashlib.sha256(j + c).hexdigest())
    return manifest, scripts


def release_notes(root: pathlib.Path, ref: str | None) -> str:
    old_manifest, old_scripts = _at_ref(root, ref)
    first = old_manifest is None
    if first:
        old_manifest, old_scripts = {"entries": []}, {}
    new_manifest = json.loads(_read(root, "manifest.json").decode("utf-8"))
    new_scripts = {
        sid: (s["meta"], s["sha256"]) for sid, s in load_scripts(root).items()
    }

    def desc(meta: dict) -> str:
        return f"{meta.get('effects')}, {meta.get('status')}"

    lines: list[str] = []

    old_schema, new_schema = old_manifest.get("schema", 1), new_manifest.get("schema", 1)
    if not first and old_schema != new_schema:
        lines += [f"## Format change: schema {old_schema} → {new_schema}", ""]
        lines += FORMAT_CHANGES.get((old_schema, new_schema),
                                    ["The package format changed; see CONTRIBUTING.md for the new one."])
        lines.append("")

    script_lines = []
    for sid in sorted(set(old_scripts) | set(new_scripts)):
        if sid not in old_scripts:
            script_lines.append(f"- added `{sid}` ({desc(new_scripts[sid][0])})")
        elif sid not in new_scripts:
            script_lines.append(f"- removed `{sid}`")
        elif old_scripts[sid][1] != new_scripts[sid][1]:
            script_lines.append(f"- changed `{sid}` ({desc(new_scripts[sid][0])})")
    if script_lines:  # the heading appears only when something changed
        lines += ["## Scripts changed", "", *script_lines, ""]

    # Entry-level statuses: both schemas give one per entry.
    old_e = {e["id"]: e for e in old_manifest["entries"]}
    new_e = {e["id"]: e for e in new_manifest["entries"]}
    added = [new_e[i] for i in new_e if i not in old_e]
    removed = [old_e[i] for i in old_e if i not in new_e]
    changed = [(i, old_e[i]["status"], new_e[i]["status"])
               for i in new_e if i in old_e and old_e[i]["status"] != new_e[i]["status"]]

    lines += ["## Entries", ""]
    if not (added or removed or changed):
        lines.append("No changes.")
    if added:
        lines.append(f"- {len(added)} new:")
        lines += [f"  - {e['title']} ({e['status']})" for e in added]
    if changed:
        lines.append("- Status changes:")
        lines += [f"  - `{i}`: {a} → {b}" for i, a, b in changed]
    if removed:
        lines.append("- Removed:")
        lines += [f"  - {e['title']}" for e in removed]
    return "\n".join(lines) + "\n"


def latest_tag(root: pathlib.Path) -> str | None:
    """The newest v* tag reachable from HEAD, or None (no tags, or a shallow clone)."""
    out = git(root, "describe", "--tags", "--abbrev=0", "--match", "v*", "HEAD")
    return out.strip() if out and out.strip() else None


# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", required=True, help="e.g. 2.0.0 (no leading v)")
    ap.add_argument("--out", default="dist", help="output directory (default: dist)")
    ap.add_argument("--notes-from", metavar="REF",
                    help="previous git tag; also write release-notes.md against it")
    ap.add_argument("--root", default=str(ROOT), help="repo root (default: this repo)")
    args = ap.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    out = pathlib.Path(args.out)
    try:
        dest, warnings = build(root, args.version, out)
        for w in warnings:
            print(f"warning: {w}", file=sys.stderr)
        print(f"{dest} ({dest.stat().st_size} bytes)")
        if args.notes_from is not None:
            notes = out / "release-notes.md"
            notes.write_text(release_notes(root, args.notes_from or None), encoding="utf-8")
            print(notes)
    except BuildError as exc:
        print(f"package not built: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
