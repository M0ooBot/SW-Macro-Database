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
RECORD = {"subject": "cat-01-demo", "language": "csharp", "swRevision": "32.5.0", "major": 32,
          "date": "2026-11-25", "method": "smoke", "result": "pass", "scope": "full", "observed": "Ran."}


class ManifestTests(unittest.TestCase):
    def make(self, ev="", rec="", recipe_status="null", sidecar=None, records=(), **replace):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name)
        text = ENTRY.format(ev=ev, rec=rec, recipe_status=recipe_status)
        for old, new in replace.items():
            text = text.replace(old, new)
        (root / "entries" / "cat").mkdir(parents=True)
        (root / "entries" / "cat" / "01-demo.md").write_text(text, encoding="utf-8")
        if sidecar is not None:
            (root / "entries" / "cat" / "01-demo.csx").write_text(sidecar, encoding="utf-8")
        (root / "evidence").mkdir()
        for rid in records:
            (root / "evidence" / f"{rid}.json").write_text(json.dumps(dict(RECORD, id=rid)), encoding="utf-8")
        (root / "INDEX.md").write_text("[demo](entries/cat/01-demo.md)\n", encoding="utf-8")
        return build_manifest.collect(root)

    def test_plain_entry(self):
        problems, manifest = self.make()
        self.assertEqual(problems, [])
        e = manifest["entries"][0]
        self.assertEqual(manifest["schema"], 2)
        self.assertEqual(list(e), ["id", "title", "path", "category", "answers", "keywords", "api", "language",
                                   "status", "verified_on", "majors", "evidence", "recipe", "superseded_by"])
        self.assertEqual((e["status"], e["majors"], e["recipe"]), ("verified", [34], None))

    def test_recipe_and_effective_majors(self):
        sidecar = "// recipe-effects: read-only\nctx.Log(ctx.Sw.RevisionNumber());\n"
        problems, manifest = self.make(ev="e-1", rec="e-2", recipe_status="verified", sidecar=sidecar,
                                       records=("e-1", "e-2"))
        self.assertEqual(problems, [])
        e = manifest["entries"][0]
        self.assertEqual(e["majors"], [32, 34])
        self.assertEqual(e["recipe"], {"path": "entries/cat/01-demo.csx", "status": "verified",
                                       "majors": [32], "evidence": ["e-2"]})

    def test_sidecar_invariant(self):
        self.assertEqual(len(self.make(recipe_status="unverified")[0]), 1)
        self.assertEqual(len(self.make(sidecar="// recipe-effects: read-only\n")[0]), 1)

    def test_rules(self):
        cases = {
            "language: [python]": "language: [csharp]",
            "majors: [34]": "majors: [32]",
            "superseded_by: null": "superseded_by: nowhere",
            "schema: 2": "schema: 1",
            "keywords: [demo]\n": "keywords: [demo]\nextra: 1\n",
        }
        for old, new in cases.items():
            problems, _ = self.make(**{old: new})
            self.assertEqual(len(problems), 1, (new, problems))

    def test_verified_needs_an_observation(self):
        problems, _ = self.make(**{"majors: [34]": "majors: []"})
        self.assertEqual(len(problems), 1, problems)

    def test_majors_named(self):
        self.assertEqual(build_manifest.majors_named("SolidWorks 2026 (34.1.1) and 2024 SP5, run 2026-11-14"), {32, 34})
        self.assertEqual(build_manifest.majors_named("Python 3.13 on Windows 11"), set())


if __name__ == "__main__":
    unittest.main()
