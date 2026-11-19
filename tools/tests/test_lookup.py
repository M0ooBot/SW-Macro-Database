import importlib.util
import pathlib
import sys
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
    def test_blocks(self):
        self.assertEqual(lookup.read_blocks(SQL), {"entries.create": "A;", "gotchas.create": "B;",
                                                   "entries.search": "C;", "gotchas.search": "D;"})

    def test_refused(self):
        for bad in (SQL.replace("@format 1", "@format 2"),
                    SQL.replace("-- @block gotchas.search\nD;\n", ""),
                    SQL + "-- @block extra\nE;\n",
                    SQL + "-- @block entries.create\nA;\n"):
            with self.assertRaises(lookup.PackageError):
                lookup.read_blocks(bad)


class MatchTests(unittest.TestCase):
    def test_none(self):
        self.assertIsNone(lookup.match_text(" -- ; "))

    def test_dedupe_is_ascii_only(self):
        self.assertEqual(lookup.match_text("Ab aB É é"), '"Ab"* OR "É"* OR "é"*')


if __name__ == "__main__":
    unittest.main()
