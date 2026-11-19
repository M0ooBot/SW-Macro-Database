#!/usr/bin/env python3
"""Search this SolidWorks macro database without SW-Agent.

    python3 lookup.py "how do I export a body to STEP"
    python3 lookup.py "SaveAs3 overwrite" -k 10 --json
    python3 lookup.py --gotchas "rebuild"
    python3 lookup.py --always
    python3 lookup.py --self-test

It builds a full-text index in memory from manifest.json, the entry files,
gotchas.json and the gotcha files, with the table definitions and ranking
queries in search.sql (the same text SW-Agent's db_search runs, so both rank
alike), and prints ranked ids, statuses and titles. It never writes a file.
--self-test runs search-tests.json: the match-text vectors and the test
questions, each of which must find its entry in the top 5.

It looks for the package beside itself (the release's skill folder), else two
folders up (the repository); --root names another folder holding manifest.json.

Needs Python 3.9 or later whose SQLite has FTS5 (python.org builds and
Ubuntu's do). Standard library only.

Exit codes: 0 answered (with results or none), 1 a self-test failure, 2 no
FTS5, 3 the package cannot be read, 4 bad arguments.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
SQL_FORMAT = "1"
BLOCKS = ("entries.create", "gotchas.create", "entries.search", "gotchas.search")
NO_FTS5 = "this Python's SQLite has no FTS5; use python.org Python 3.9 or later"
TOKEN = {"Lu", "Ll", "Lt", "Lm", "Lo", "Nd", "Nl", "No", "Co"}
MARK = {"Mn", "Mc", "Me"}
ASCII_LOWER = {c: c + 32 for c in range(ord("A"), ord("Z") + 1)}


class PackageError(Exception):
    """The package cannot be read; the message names the file."""


# --------------------------------------------------------------------------
# the contract shared with SW-Agent: match text, block file, column content


def match_text(query: str):
    """The FTS5 MATCH expression for free text, or None when it has no tokens.

    Tokens are runs of letters, numbers and private-use characters, continued
    by combining marks once started. A token equal to an earlier one after
    ASCII-only lower-casing is dropped. Each is quoted (quotes doubled), given
    a trailing *, and the tokens are joined with OR.
    """
    tokens, current = [], []
    for ch in query:
        cat = unicodedata.category(ch)
        if cat in TOKEN or (current and cat in MARK):
            current.append(ch)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    seen, kept = set(), []
    for t in tokens:
        key = t.translate(ASCII_LOWER)
        if key not in seen:
            seen.add(key)
            kept.append(t)
    if not kept:
        return None
    return " OR ".join('"' + t.replace('"', '""') + '"*' for t in kept)


def read_blocks(text: str) -> dict:
    """search.sql's named blocks: exactly BLOCKS, after a known format line."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines or lines[0].strip() != "-- @format " + SQL_FORMAT:
        raise PackageError(f"search.sql: the first line must be '-- @format {SQL_FORMAT}'")
    blocks, name = {}, None
    for line in lines[1:]:
        if line.startswith("-- @block "):
            name = line[len("-- @block "):].strip()
            if name in blocks:
                raise PackageError(f"search.sql: block {name!r} appears twice")
            blocks[name] = []
        elif name is not None:
            blocks[name].append(line)
        elif line.strip():
            raise PackageError("search.sql: text before the first block")
    if sorted(blocks) != sorted(BLOCKS):
        raise PackageError(f"search.sql: the blocks must be exactly {list(BLOCKS)}, found {list(blocks)}")
    return {k: "\n".join(v).strip() for k, v in blocks.items()}


def body_of(markdown: str) -> str:
    """A file's text without its frontmatter: newlines normalised to LF, and
    everything up to and including the closing --- line removed (a closing
    --- at the very end counts)."""
    text = markdown.replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 3)
    if end >= 0:
        return text[end + 5:]
    if len(text) >= 7 and text.endswith("\n---"):
        return ""
    return text


# --------------------------------------------------------------------------


def find_root(explicit) -> pathlib.Path:
    if explicit:
        return pathlib.Path(explicit).resolve()
    for candidate in (HERE, HERE.parent.parent):
        if (candidate / "manifest.json").is_file():
            return candidate
    raise PackageError(f"no manifest.json beside {HERE} or two folders up; pass --root")


def read_text(path: pathlib.Path, root: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PackageError(f"{path.relative_to(root).as_posix() if path.is_relative_to(root) else path}: {exc}")


def read_json(path: pathlib.Path, root: pathlib.Path):
    try:
        return json.loads(read_text(path, root))
    except ValueError as exc:
        raise PackageError(f"{path.name}: not valid JSON ({exc})")


class Package:
    def __init__(self, root: pathlib.Path):
        self.root = root
        self.blocks = read_blocks(read_text(HERE / "search.sql", HERE))
        manifest = read_json(root / "manifest.json", root)
        gotchas = read_json(root / "gotchas.json", root)
        try:
            if manifest["schema"] != 2 or gotchas["schema"] != 1:
                raise PackageError("manifest.json must be schema 2 and gotchas.json schema 1")
            self.entries = manifest["entries"]
            self.gotchas = gotchas["gotchas"]
            self.by_id = {e["id"]: e for e in self.entries}
            self.by_number = {g["number"]: g for g in self.gotchas}
        except (KeyError, TypeError) as exc:
            raise PackageError(f"manifest.json or gotchas.json lacks {exc}")

    def index(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        try:
            conn.execute(self.blocks["entries.create"])
            conn.execute(self.blocks["gotchas.create"])
        except sqlite3.OperationalError as exc:
            conn.close()
            if "fts5" in str(exc).lower():
                raise RuntimeError(NO_FTS5)
            raise PackageError(f"search.sql: {exc}")
        for e in self.entries:
            body = body_of(read_text(self.root / e["path"], self.root))
            conn.execute("INSERT INTO entries (id, title, answers, keywords, api, body) VALUES (?, ?, ?, ?, ?, ?)",
                         (e["id"], e["title"], e["answers"], " ".join(e["keywords"]), " ".join(e["api"]), body))
        for g in sorted(self.gotchas, key=lambda g: g["number"]):
            body = body_of(read_text(self.root / g["path"], self.root))
            conn.execute("INSERT INTO gotchas (number, title, body) VALUES (?, ?, ?)", (int(g["number"]), g["title"], body))
        return conn


def has_fts5() -> bool:
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE VIRTUAL TABLE probe USING fts5(x)")
        return True
    except sqlite3.OperationalError:
        return False
    finally:
        conn.close()


def search(conn: sqlite3.Connection, sql: str, query: str, k: int) -> list:
    q = match_text(query)
    if q is None:
        return []
    return [row[0] for row in conn.execute(sql, {"q": q, "k": k})]


# --------------------------------------------------------------------------


def self_test(pkg: Package, conn: sqlite3.Connection, out) -> bool:
    tests = read_json(HERE / "search-tests.json", HERE)
    if not isinstance(tests, dict) or tests.get("format") != 1:
        raise PackageError("search-tests.json: 'format' must be 1")
    failures = 0
    for v in tests["match"]:
        got = match_text(v["query"])
        if got != v["text"]:
            failures += 1
            print(f"match FAIL {v['query']!r}: expected {v['text']!r}, got {got!r}", file=out)
    for t in tests["questions"]:
        ids = search(conn, pkg.blocks["entries.search"], t["question"], 5)
        if t["expect"] not in ids:
            failures += 1
            print(f"question FAIL {t['question']!r}: expected {t['expect']} in the top 5, got {ids}", file=out)
    print(f"self-test: {len(tests['match'])} match vectors, {len(tests['questions'])} questions, "
          f"{failures} failure(s)", file=out)
    return failures == 0


def entry_result(pkg: Package, rank: int, eid: str) -> dict:
    e = pkg.by_id[eid]
    return {"id": eid, "status": e["status"], "title": e["title"], "rank": rank}


def gotcha_result(pkg: Package, rank: int, number: int) -> dict:
    g = pkg.by_number[number]
    return {"number": number, "title": g["title"], "rank": rank}


def print_results(pkg: Package, results: list, gotchas: bool) -> None:
    if not results:
        print("No gotchas match." if gotchas else "No entries match.")
    for r in results:
        if gotchas:
            g = pkg.by_number[r["number"]]
            flag = "  [always]" if g["always"] else ""
            print(f"{r['rank']}. G{r['number']}{flag}  {r['title']}\n   {g['path']}")
        else:
            e = pkg.by_id[r["id"]]
            recipe = f", C# recipe {e['recipe']['status']}" if e.get("recipe") else ""
            print(f"{r['rank']}. {r['id']}  [{r['status']}{recipe}]  {r['title']}\n   {e['path']}")


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"lookup.py: {message}", file=sys.stderr)
        sys.exit(4)


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = Parser(description="Search the SolidWorks macro database (stand-alone).")
    ap.add_argument("question", nargs="?", help="what you want to do, in your own words or API names")
    ap.add_argument("-k", type=int, default=5, help="how many results (default 5)")
    ap.add_argument("--gotchas", metavar="TOPIC", help="search the gotchas instead")
    ap.add_argument("--always", action="store_true", help="list the always-list of gotchas")
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--self-test", action="store_true", help="run search-tests.json")
    ap.add_argument("--root", help="the folder holding manifest.json (default: found automatically)")
    args = ap.parse_args(argv)
    modes = [args.question is not None, args.gotchas is not None, args.always, args.self_test]
    if sum(modes) != 1:
        ap.error("give exactly one of: a question, --gotchas TOPIC, --always, --self-test")
    if not 1 <= args.k <= 100:
        ap.error("-k must be 1 to 100")

    if not has_fts5():
        print(NO_FTS5, file=sys.stderr)
        return 2
    try:
        pkg = Package(find_root(args.root))
        if args.always:
            results = [gotcha_result(pkg, i, g["number"])
                       for i, g in enumerate(sorted((g for g in pkg.gotchas if g["always"]), key=lambda g: g["number"]), 1)]
            query, gotchas = "always", True
        else:
            conn = pkg.index()
            if args.self_test:
                return 0 if self_test(pkg, conn, sys.stdout) else 1
            if args.gotchas is not None:
                ids = search(conn, pkg.blocks["gotchas.search"], args.gotchas, args.k)
                results = [gotcha_result(pkg, i, n) for i, n in enumerate(ids, 1)]
                query, gotchas = args.gotchas, True
            else:
                ids = search(conn, pkg.blocks["entries.search"], args.question, args.k)
                results = [entry_result(pkg, i, eid) for i, eid in enumerate(ids, 1)]
                query, gotchas = args.question, False
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2
    except (PackageError, KeyError, TypeError, sqlite3.Error) as exc:
        print(f"lookup.py: the package cannot be read: {exc}", file=sys.stderr)
        return 3
    if args.json:
        print(json.dumps({"format": 1, "query": query, "results": results}, ensure_ascii=False, indent=2))
    else:
        print_results(pkg, results, gotchas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
