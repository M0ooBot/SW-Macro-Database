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

--root names the skill folder to read: by default the folder this script is
in, or, in a clone of the repository where nothing is beside it, the
repository root (two folders up). search.sql and search-tests.json are read
from the root when it has them, else from beside this script. Every file is
read as strict UTF-8 without a byte-order mark.

--json prints {"format": 1, "query": ..., "results": [{"id", "status", "title",
"rank"}]}; gotcha results carry "number" for "id" and no "status".

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
# .NET's char.IsWhiteSpace (what SW-Agent's SearchSql trims), not str.isspace: Python
# also counts U+001C-U+001F, so search.sql is read with this set for exact parity.
WHITESPACE = "".join(chr(c) for c in [*range(0x09, 0x0E), 0x20, 0x85, 0xA0, 0x1680, *range(0x2000, 0x200B),
                                       0x2028, 0x2029, 0x202F, 0x205F, 0x3000])


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
    """search.sql's named blocks, read as SW-Agent's SearchSql.Parse reads them.

    The first line is '-- @format 1'; only blank lines come before the first
    block; each block runs to the next '-- @block' line or the end and holds
    exactly one statement (comments allowed); the blocks are exactly BLOCKS.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines[0].startswith("-- @format "):
        raise PackageError(f"search.sql: the first line must be '-- @format {SQL_FORMAT}'")
    fmt = lines[0][len("-- @format "):].strip(WHITESPACE)
    if fmt != SQL_FORMAT:
        raise PackageError(f"search.sql: format {fmt} is not supported; this lookup.py reads format {SQL_FORMAT}")
    blocks: dict = {}
    name, body = None, []

    def close():
        if name is None:
            return
        statement = "\n".join(body).strip(WHITESPACE)
        code, one = has_code(statement)
        if not code:
            raise PackageError(f"search.sql: block {name!r} is empty")
        if not one:
            raise PackageError(f"search.sql: block {name!r} holds more than one statement")
        blocks[name] = statement

    for i, line in enumerate(lines[1:], 2):
        if line.startswith("-- @block "):
            close()
            name, body = line[len("-- @block "):].strip(WHITESPACE), []
            if name not in BLOCKS:
                raise PackageError(f"search.sql: unknown block {name!r}; the blocks are {', '.join(BLOCKS)}")
            if name in blocks:
                raise PackageError(f"search.sql: block {name!r} appears twice")
        elif name is not None:
            body.append(line)
        elif line.strip(WHITESPACE):
            raise PackageError(f"search.sql: line {i} is outside every block")
    close()
    missing = [b for b in BLOCKS if b not in blocks]
    if missing:
        raise PackageError(f"search.sql: block {', '.join(repr(m) for m in missing)} is missing")
    return blocks


def has_code(sql: str):
    """(code, one statement): whether SQL holds code outside comments, and whether
    nothing but whitespace and comments follows its first ';' outside quotes."""
    code = ended = False
    one = True
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if sql.startswith("--", i):
            end = sql.find("\n", i)
            i = n if end < 0 else end + 1
            continue
        if sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        if c in WHITESPACE:
            i += 1
            continue
        if ended:
            one = False
        if c == ";":
            ended = code
            i += 1
            continue
        code = True
        close = {"'": "'", '"': '"', "\x60": "\x60", "[": "]"}.get(c)
        i += 1
        if close is None:
            continue
        # A quoted literal or name; a doubled closing quote stays inside it.
        while i < n:
            if sql[i] == close and not (close != "]" and i + 1 < n and sql[i + 1] == close):
                break
            i += 2 if sql[i] == close else 1
        i += 1
    return code, one


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
    """A package text file: UTF-8 without a byte-order mark, decoded strictly."""
    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise PackageError(f"{rel}: cannot be read ({exc.strerror or exc})")
    if data.startswith(b"\xef\xbb\xbf"):
        raise PackageError(f"{rel}: starts with a byte-order mark; package files are UTF-8 without one")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PackageError(f"{rel}: not valid UTF-8 ({exc.reason} at byte {exc.start})")


def read_json(path: pathlib.Path, root: pathlib.Path):
    try:
        return json.loads(read_text(path, root))
    except ValueError as exc:
        raise PackageError(f"{path.name}: not valid JSON ({exc})")


def beside(root: pathlib.Path, name: str) -> pathlib.Path:
    """search.sql and search-tests.json: the package's own when the root has them
    (a release's skill folder), else the ones beside this script (the repository)."""
    return root / name if (root / name).is_file() else HERE / name


class Package:
    def __init__(self, root: pathlib.Path):
        self.root = root
        sql = beside(root, "search.sql")
        self.blocks = read_blocks(read_text(sql, sql.parent))
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
        try:
            for e in self.entries:
                body = body_of(read_text(self.root / e["path"], self.root))
                conn.execute("INSERT INTO entries (id, title, answers, keywords, api, body) VALUES (?, ?, ?, ?, ?, ?)",
                             (e["id"], e["title"], e["answers"], " ".join(e["keywords"]), " ".join(e["api"]), body))
            for g in sorted(self.gotchas, key=lambda g: g["number"]):
                body = body_of(read_text(self.root / g["path"], self.root))
                conn.execute("INSERT INTO gotchas (number, title, body) VALUES (?, ?, ?)", (int(g["number"]), g["title"], body))
        except BaseException:
            conn.close()
            raise
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
    path = beside(pkg.root, "search-tests.json")
    tests = read_json(path, path.parent)
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
    ap.add_argument("--root", help="the skill folder to read (default: this script's folder, or the "
                                   "repository root in a clone where nothing is beside it)")
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
