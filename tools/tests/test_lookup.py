import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

LOOKUP = pathlib.Path(__file__).resolve().parents[2] / "skills" / "sw-macro-database" / "lookup.py"
spec = importlib.util.spec_from_file_location("repo_lookup", LOOKUP)
lookup = importlib.util.module_from_spec(spec)
sys.dont_write_bytecode, _was = True, sys.dont_write_bytecode
spec.loader.exec_module(lookup)
sys.dont_write_bytecode = _was

SQL = "-- @format 1\n-- @block entries.create\nA;\n-- @block gotchas.create\nB;\n-- @block entries.search\nC;\n-- @block gotchas.search\nD;\n"


class BodyTests(unittest.TestCase):
    def test_front_matter_cut(self):
        self.assertEqual(lookup.body_of("---\nid: a\n---\nBody\n"), "Body\n")
        self.assertEqual(lookup.body_of("---\r\nid: a\r\n---\r\nBody\rmore\r\n"), "Body\nmore\n")
        self.assertEqual(lookup.body_of("---\nid: a\n---"), "")
        self.assertEqual(lookup.body_of("No front matter\n"), "No front matter\n")
        self.assertEqual(lookup.body_of("---\nnever closed\n"), "---\nnever closed\n")


class BlockTests(unittest.TestCase):
    """The same files SW-Agent's SearchSql.Parse refuses, refused the same way."""

    def test_blocks(self):
        self.assertEqual(lookup.read_blocks(SQL), {"entries.create": "A;", "gotchas.create": "B;",
                                                   "entries.search": "C;", "gotchas.search": "D;"})

    def test_crlf_blank_lines_comments_in_a_block_and_several_lines(self):
        text = SQL.replace("-- @block gotchas.search\n", "-- @block gotchas.search\n-- best first\n")
        text = text.replace("-- @format 1\n", "-- @format 1\n\n").replace("D;", "SELECT 1\nFROM t;")
        text = text.replace("\n", "\r\n")
        self.assertEqual(lookup.read_blocks(text)["gotchas.search"], "-- best first\nSELECT 1\nFROM t;")

    def test_refused(self):
        cases = [
            (("-- @block gotchas.search", "-- @block gotchas.find"), "unknown block 'gotchas.find'"),
            (("-- @block gotchas.create", "-- @block entries.create"), "'entries.create' appears twice"),
            (("-- @format 1", "-- @format 2"), "format 2 is not supported"),
            (("-- @format 1", "-- format 1"), "the first line must be"),
            (("-- @format 1\n", "-- @format 1\nPRAGMA x;\n"), "line 2 is outside every block"),
            (("-- @format 1\n", "-- @format 1\n\n-- The index.\n"), "line 3 is outside every block"),
            (("C;", "C; DROP TABLE x;"), "'entries.search' holds more than one statement"),
            (("D;", "D;;"), "'gotchas.search' holds more than one statement"),
            (("-- @block gotchas.search\nD;\n", ""), "'gotchas.search' is missing"),
            (("D;", "-- only a comment"), "'gotchas.search' is empty"),
            (("D;", ""), "'gotchas.search' is empty"),
        ]
        for (old, new), message in cases:
            with self.subTest(new=new):
                text = SQL.replace(old, new)
                self.assertNotEqual(text, SQL)
                with self.assertRaises(lookup.PackageError) as caught:
                    lookup.read_blocks(text)
                self.assertIn(message, str(caught.exception))

    def test_has_code(self):
        cases = {
            "SELECT 1": (True, True),
            "SELECT 1;": (True, True),
            "-- why\nSELECT 1; -- done\n/* and */  ": (True, True),
            "SELECT ';' AS a, \"b;\", [c;], \x60d;\x60 FROM t WHERE x = 'it''s;';": (True, True),
            "SELECT 1; SELECT 2": (True, False),
            "SELECT 1;;": (True, False),
            "SELECT 1 /* ; */ ; -- ;\n": (True, True),
            "-- only a comment\n": (False, True),
            "": (False, True),
        }
        for sql, expected in cases.items():
            with self.subTest(sql=sql):
                self.assertEqual(lookup.has_code(sql), expected)

    def test_whitespace_is_dotnets(self):
        # U+001C-U+001F are whitespace to Python's str.strip, not to .NET's Trim:
        # a line holding one is outside every block, as SearchSql.Parse says.
        with self.assertRaises(lookup.PackageError) as caught:
            lookup.read_blocks(SQL.replace("-- @format 1\n", "-- @format 1\n" + chr(0x1C) + "\n"))
        self.assertIn("line 2 is outside every block", str(caught.exception))
        self.assertEqual(lookup.has_code(chr(0x1F)), (True, True))
        wrapped = SQL.replace("C;", chr(0x3000) + "C;" + chr(0x2028))
        self.assertEqual(lookup.read_blocks(wrapped), lookup.read_blocks(SQL))


class PackageTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)
        (self.root / "entries").mkdir()
        (self.root / "gotchas").mkdir()
        (self.root / "entries" / "01-a.md").write_text("---\nid: a\n---\nAlpha body\n", encoding="utf-8")
        (self.root / "gotchas" / "001-g.md").write_text("---\nid: G1\n---\n\nGamma body\n", encoding="utf-8")
        (self.root / "manifest.json").write_text(json.dumps({"schema": 2, "entries": [
            {"id": "a", "title": "Alpha", "answers": "How?", "keywords": [], "api": [], "path": "entries/01-a.md",
             "status": "verified", "recipe": None}]}), encoding="utf-8")
        (self.root / "gotchas.json").write_text(json.dumps({"schema": 1, "gotchas": [
            {"number": 1, "title": "Gamma", "always": True, "path": "gotchas/001-g.md"}]}), encoding="utf-8")

    def search(self, query):
        package = lookup.Package(self.root)
        conn = package.index()
        try:
            return lookup.search(conn, package.blocks["entries.search"], query, 5)
        finally:
            conn.close()

    def test_reads_the_roots_own_search_sql(self):
        self.assertEqual(self.search("alpha"), ["a"])
        (self.root / "search.sql").write_text(SQL, encoding="utf-8")
        self.assertEqual(lookup.Package(self.root).blocks["entries.search"], "C;")

    def test_a_bom_in_a_package_file_is_refused(self):
        path = self.root / "entries" / "01-a.md"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        with self.assertRaises(lookup.PackageError) as caught:
            self.search("alpha")
        self.assertIn("entries/01-a.md: starts with a byte-order mark", str(caught.exception))


class MatchTests(unittest.TestCase):
    def test_none(self):
        self.assertIsNone(lookup.match_text(" -- ; "))

    def test_astral_letters_are_one_token(self):
        self.assertEqual(lookup.match_text("\U0001d400\U0001d401c x"), '"\U0001d400\U0001d401c"* OR "x"*')

    def test_dedupe_is_ascii_only(self):
        self.assertEqual(lookup.match_text("Ab aB É é"), '"Ab"* OR "É"* OR "é"*')


if __name__ == "__main__":
    unittest.main()
