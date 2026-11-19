"""Checks that need a whole repository: a copy of this one, changed one way each time."""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

import build_package
import validate

ROOT = pathlib.Path(__file__).resolve().parents[2]
IGNORE = shutil.ignore_patterns(".git", "dist", "__pycache__", "*.pyc")


class RepoCopyTests(unittest.TestCase):
    """Each test changes one thing in a copy of this repository and checks only that.

    A problem already in the tree is validate's to report, once: when the
    unchanged copy does not build, or its generated files are not current,
    the tests that need it are skipped rather than failing with it.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.pristine = pathlib.Path(cls._tmp.name) / "repo"
        shutil.copytree(ROOT, cls.pristine, ignore=IGNORE)
        try:
            build_package.assemble(cls.pristine, "0.0.0-test")
            cls.unbuildable = None
        except build_package.BuildError:
            cls.unbuildable = "the tree itself does not build; validate says why"
        cls.not_current = ("the tree's generated files are not current; validate says why"
                           if validate.check_generated(cls.pristine) else None)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def copy(self, needs: str | None) -> pathlib.Path:
        if needs:
            self.skipTest(needs)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name) / "repo"
        shutil.copytree(self.pristine, root)
        return root

    def test_a_package_file_with_a_bom_or_bad_utf8_is_refused(self):
        for name, data in (("bom", b"\xef\xbb\xbf"), ("bad", b"\xff\xfe")):
            with self.subTest(name):
                root = self.copy(self.unbuildable)
                path = root / "code" / "csharp" / "StaComRunner.cs"
                path.write_bytes(data + path.read_bytes() if name == "bom" else path.read_bytes() + data)
                with self.assertRaises(build_package.BuildError) as caught:
                    build_package.assemble(root, "0.0.0-test")
                self.assertIn("skills/sw-macro-database/code/csharp/StaComRunner.cs", str(caught.exception))

    def test_paths_equal_but_for_case_are_refused(self):
        root = self.copy(self.unbuildable)
        shutil.copy(root / "code" / "python" / "pick.py", root / "code" / "python" / "Pick.py")
        with self.assertRaises(build_package.BuildError) as caught:
            build_package.assemble(root, "0.0.0-test")
        self.assertIn("only in case", str(caught.exception))

    def test_every_generated_file_is_checked_for_staleness(self):
        for rel in ("manifest.json", "gotchas.json", "GOTCHAS.md", "API-LEDGER.md"):
            with self.subTest(rel):
                root = self.copy(self.not_current)
                with open(root / rel, "a", encoding="utf-8") as f:
                    f.write("\n")
                self.assertEqual(validate.check_generated(root),
                                 [f"{rel} is stale: run python3 tools/build_manifest.py"])


def git(root: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                    "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", "-C", str(root), *args],
                   check=True, capture_output=True)


class ReleaseNotesTests(unittest.TestCase):
    """release_notes against a previous tag, in a scratch git repository."""

    def test_format_change_scripts_and_statuses(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name)
        (root / "scripts" / "demo").mkdir(parents=True)

        def write(manifest, script_json):
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "scripts" / "demo" / "script.json").write_text(json.dumps(script_json), encoding="utf-8")
            (root / "scripts" / "demo" / "script.csx").write_text("ctx.Log(\"x\");\n", encoding="utf-8")

        write({"schema": 1, "entries": [{"id": "a-01", "title": "A", "status": "verified"},
                                        {"id": "b-01", "title": "B", "status": "verified"}]},
              {"effects": "read-only", "status": "unverified", "verified_on": None})
        git(root, "init", "-q")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "v1")
        git(root, "tag", "v1.0.0")
        write({"schema": 2, "entries": [{"id": "a-01", "title": "A", "status": "unverified"},
                                        {"id": "c-01", "title": "C", "status": "verified"}]},
              {"effects": "read-only", "status": "unverified", "evidence": []})

        self.assertEqual(build_package.latest_tag(root), "v1.0.0")
        notes = build_package.release_notes(root, "v1.0.0")
        self.assertTrue(notes.startswith("## Format change: schema 1 → 2\n"), notes)
        for line in ("- changed `demo` (read-only, unverified)", "  - C (verified)",
                     "  - `a-01`: verified → unverified", "- Removed:\n  - B"):
            self.assertIn(line.replace("`", "\x60"), notes)

        first = build_package.release_notes(root, None)
        self.assertNotIn("Format change", first)
        self.assertIn("- added \x60demo\x60", first)


if __name__ == "__main__":
    unittest.main()
