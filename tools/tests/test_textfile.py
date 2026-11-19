import json
import pathlib
import tempfile
import unittest

import evidence
import gotchas
import ledger
import textfile


class TextFileTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = pathlib.Path(tmp.name)

    def test_problem(self):
        self.assertIsNone(textfile.problem("état\r\n".encode("utf-8")))
        self.assertIn("byte-order mark", textfile.problem(b"\xef\xbb\xbfx"))
        self.assertIn("not valid UTF-8", textfile.problem(b"caf\xe9"))

    def test_read_normalises_newlines(self):
        path = self.root / "a.md"
        path.write_bytes(b"a\r\nb\rc\n")
        self.assertEqual(textfile.read(path, "a.md"), ("a\nb\nc\n", None))
        self.assertIn("cannot be read", textfile.read(self.root / "missing.md", "missing.md")[1])

    def test_gotcha_not_utf8(self):
        (self.root / "gotchas").mkdir()
        (self.root / "gotchas" / "001-x.md").write_bytes(b"\xef\xbb\xbf---\nid: G1\n---\n\nx\n")
        problems, _ = gotchas.load(self.root)
        self.assertIn("gotchas/001-x.md: starts with a byte-order mark", problems[0])

    def test_evidence_not_utf8(self):
        (self.root / "evidence").mkdir()
        (self.root / "evidence" / "e-1.json").write_bytes(json.dumps({"id": "e-1"}).encode() + b"\xff")
        problems, records = evidence.load(self.root)
        self.assertEqual(records, {})
        self.assertIn("evidence/e-1.json: not valid UTF-8", problems[0])

    def test_ledger_not_utf8(self):
        (self.root / "api-ledger.json").write_bytes(b"\xef\xbb\xbf{}")
        problems, data = ledger.load(self.root)
        self.assertIsNone(data)
        self.assertIn("api-ledger.json: starts with a byte-order mark", problems[0])


if __name__ == "__main__":
    unittest.main()
