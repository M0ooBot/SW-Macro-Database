import unittest

import build_package


class PathRuleTests(unittest.TestCase):
    def test_good(self):
        for p in ("package.json", "skills/sw-macro-database/entries/files/01-batch-convert-step.md",
                  "skills/sw-macro-database/evidence/_TEMPLATE.json", "a/b_c/x.y-z"):
            self.assertIsNone(build_package.check_path(p), p)

    def test_bad(self):
        cases = {
            "a/b c.md": "segment",
            "a/é.md": "segment",
            "a/-x/../y": "segment",
            "a/name.": "ends in",
            "a/CON": "device",
            "a/con.txt": "device",
            "a/Lpt1.md": "device",
            "/".join(["a"] * 13): "segments",
            "a/" + "x" * 150: "longer",
            "a//b": "segment",
            "a/.hidden": "segment",
        }
        for path, why in cases.items():
            self.assertIn(why, build_package.check_path(path) or "", path)

    def test_versions(self):
        for v in ("2.0.0", "0.0.0-ci", "2.1.0-rc.1+build.5"):
            self.assertTrue(build_package.VERSION_RE.match(v), v)
        for v in ("v2.0.0", "2.0", "01.0.0", "2.0.0-01", "2.0.0+"):
            self.assertFalse(build_package.VERSION_RE.match(v), v)


class SkillTests(unittest.TestCase):
    def test_always_list(self):
        gotchas = {"gotchas": [
            {"number": 2, "title": "Metres", "always": True, "path": "gotchas/002-metres.md"},
            {"number": 3, "title": "Other", "always": False, "path": "gotchas/003-other.md"},
        ]}
        self.assertEqual(build_package.render_always(gotchas), "- **G2** [Metres](gotchas/002-metres.md)")

    def test_placeholders_filled_once(self):
        template = "{{VERSION}} {{ALWAYS}} {{SCRIPTS}} {{INDEX}}"
        manifest = {"entries": [{"category": "c", "path": "entries/c/01.md", "status": "verified",
                                 "answers": "{{VERSION}}?", "recipe": None}]}
        out = build_package.render_skill(template, "2.0.0", manifest, {"gotchas": []}, {})
        self.assertTrue(out.startswith("2.0.0 No gotcha"))
        self.assertIn("{{VERSION}}?", out)


if __name__ == "__main__":
    unittest.main()
