import json
import pathlib
import tempfile
import unittest

import build_manifest

ENTRY = """---
schema: 2
id: cat-01-demo
title: A demo
answers: "How do I demo?"
keywords: [demo]
api: [IModelDoc2.GetTitle]
language: [python]
status: verified
verified_on: "SolidWorks 2026 (34.1.1)"
majors: [34]
evidence: [{ev}]
recipe_status: {recipe_status}
recipe_evidence: [{rec}]
superseded_by: null
---

# A demo
"""
RECORD = {"subject": "cat-01-demo", "language": "python", "swRevision": "32.5.0", "major": 32,
          "date": "2026-11-25", "method": "manual", "result": "pass", "scope": "full", "observed": "Ran."}
SMOKE = {"language": "csharp", "method": "smoke"}
SIDECAR = "// recipe-effects: read-only\nctx.Log(ctx.Sw.RevisionNumber());\n"


class ManifestTests(unittest.TestCase):
    def make(self, ev="", rec="", recipe_status="null", sidecar=None, records=None, raw=None, **replace):
        """collect() on a one-entry repo; records maps an id to overrides of RECORD."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name)
        text = ENTRY.format(ev=ev, rec=rec, recipe_status=recipe_status)
        for old, new in replace.items():
            self.assertIn(old, text)
            text = text.replace(old, new)
        (root / "entries" / "cat").mkdir(parents=True)
        (root / "entries" / "cat" / "01-demo.md").write_bytes(raw if raw is not None else text.encode("utf-8"))
        if sidecar is not None:
            (root / "entries" / "cat" / "01-demo.csx").write_text(sidecar, encoding="utf-8")
        (root / "evidence").mkdir()
        for rid, changes in (records or {}).items():
            data = dict(RECORD, id=rid, **changes)
            (root / "evidence" / f"{rid}.json").write_text(json.dumps(data), encoding="utf-8")
        (root / "INDEX.md").write_text("[demo](entries/cat/01-demo.md)\n", encoding="utf-8")
        return build_manifest.collect(root)

    def assertOneProblem(self, result, fragment, count=1):
        problems, manifest = result
        self.assertEqual(len(problems), count, problems)
        self.assertTrue(any(fragment in p for p in problems), problems)
        self.assertIsNone(manifest)

    def test_plain_entry(self):
        problems, manifest = self.make()
        self.assertEqual(problems, [])
        e = manifest["entries"][0]
        self.assertEqual(manifest["schema"], 2)
        self.assertEqual(list(e), ["id", "title", "path", "category", "answers", "keywords", "api", "language",
                                   "status", "verified_on", "majors", "evidence", "recipe", "superseded_by"])
        self.assertEqual((e["status"], e["majors"], e["recipe"]), ("verified", [34], None))

    def test_recipe_and_effective_majors(self):
        problems, manifest = self.make(ev="e-1", rec="e-2", recipe_status="verified", sidecar=SIDECAR,
                                       records={"e-1": {}, "e-2": dict(SMOKE, major=33, swRevision="33.0.0")})
        self.assertEqual(problems, [])
        e = manifest["entries"][0]
        self.assertEqual(e["majors"], [32, 34])
        self.assertEqual(e["recipe"], {"path": "entries/cat/01-demo.csx", "status": "verified",
                                       "majors": [33], "evidence": ["e-2"]})

    def test_a_partial_pass_does_not_widen_majors(self):
        problems, manifest = self.make(ev="e-1", rec="e-2", recipe_status="unverified", sidecar=SIDECAR,
                                       records={"e-1": {"scope": "partial"}, "e-2": dict(SMOKE, scope="partial")})
        self.assertEqual(problems, [])
        e = manifest["entries"][0]
        self.assertEqual((e["majors"], e["recipe"]["majors"]), ([34], []))

    def test_a_failed_run_does_not_widen_majors(self):
        problems, manifest = self.make(ev="e-1", records={"e-1": {"result": "fail"}})
        self.assertEqual((problems, manifest["entries"][0]["majors"]), ([], [34]))

    def test_evidence_references(self):
        self.assertOneProblem(self.make(ev="nope"), "is not a valid evidence/nope.json")
        self.assertOneProblem(self.make(ev="e-1", records={"e-1": {"subject": "other-01-x"}}), "whose subject is", count=2)
        self.assertOneProblem(self.make(ev="e-1", records={"e-1": SMOKE}), "goes in recipe_evidence")
        self.assertOneProblem(self.make(rec="e-2", recipe_status="unverified", sidecar=SIDECAR,
                                        records={"e-2": {"language": "python"}}), "not 'csharp'")

    def test_a_verified_recipe_needs_a_smoke_record(self):
        self.assertOneProblem(self.make(rec="e-2", recipe_status="verified", sidecar=SIDECAR,
                                        records={"e-2": dict(SMOKE, method="probe")}), "method 'smoke'")

    def test_sidecar_invariant(self):
        self.assertOneProblem(self.make(recipe_status="unverified"), "there is no 01-demo.csx")
        self.assertOneProblem(self.make(sidecar="// recipe-effects: read-only\n"), "'recipe_status' must be one of")

    def test_rules(self):
        cases = {
            ("language: [python]", "language: [csharp]"): "csharp-standalone",
            ("language: [python]", "language: [cobol]"): "is not one of",
            ("majors: [34]", "majors: [32]"): "not named in verified_on",
            ("majors: [34]", "majors: [100]"): "not a revision major",
            ("superseded_by: null", "superseded_by: nowhere"): "not another entry's id",
            ("status: verified", "status: superseded"): "superseded_by",
            ("schema: 2", "schema: 1"): "'schema' must be 2",
            ("keywords: [demo]\n", "keywords: [demo]\nextra: 1\n"): "unknown field 'extra'",
            ("title: A demo\nanswers: \"How do I demo?\"", "answers: \"How do I demo?\"\ntitle: A demo"): "in this order",
        }
        for (old, new), fragment in cases.items():
            with self.subTest(new=new):
                self.assertOneProblem(self.make(**{old: new}), fragment)

    def test_languages_accepted(self):
        problems, manifest = self.make(**{"language: [python]": "language: [csharp-standalone, vba]"})
        self.assertEqual(problems, [])
        self.assertEqual(manifest["entries"][0]["language"], ["csharp-standalone", "vba"])

    def test_verified_needs_an_observation(self):
        self.assertOneProblem(self.make(**{"majors: [34]": "majors: []"}), "needs an observation")

    def test_text_that_is_not_utf8_is_a_problem_not_a_crash(self):
        good = ENTRY.format(ev="", rec="", recipe_status="null").encode("utf-8")
        self.assertOneProblem(self.make(raw=b"\xef\xbb\xbf" + good), "byte-order mark")
        self.assertOneProblem(self.make(raw=good + b"\xff\xfe"), "not valid UTF-8")

    def test_majors_named(self):
        self.assertEqual(build_manifest.majors_named("SolidWorks 2026 (34.1.1) and 2024 SP5, run 2026-11-14"), {32, 34})
        self.assertEqual(build_manifest.majors_named("Python 3.13 on Windows 11"), set())


if __name__ == "__main__":
    unittest.main()
