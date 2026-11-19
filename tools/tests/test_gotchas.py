import unittest

import gotchas

G = [
    {"number": 1, "id": "G1", "title": "`Foo` is *odd*", "always": True, "members": ["IModelDoc2.Foo"],
     "languages": ["all"], "path": "gotchas/001-foo-is-odd.md",
     "body": "See [connect/01](../entries/connect/01-a.md) and [§2](002-bar.md).\n"},
    {"number": 2, "id": "G2", "title": "Bar", "always": False, "members": [], "languages": ["pywin32"],
     "path": "gotchas/002-bar.md", "body": "Text.\n\n```python\n## not a heading\n```\n"},
]


class GotchaTests(unittest.TestCase):
    def test_render_md(self):
        md = gotchas.render_md(G)
        self.assertTrue(md.startswith(gotchas.PREAMBLE))
        self.assertIn("\n## 1. `Foo` is *odd*\n\nSee [connect/01](entries/connect/01-a.md) and [§2](#2-bar).\n", md)
        self.assertTrue(md.endswith("\n## 2. Bar\n\nText.\n\n```python\n## not a heading\n```\n"))

    def test_links_round_trip(self):
        body = G[0]["body"]
        self.assertEqual(gotchas.file_links(gotchas.root_links(body, G), G), body)

    def test_anchor_and_slug(self):
        self.assertEqual(gotchas.anchor("55. A member *or an array* comes back"), "55-a-member-or-an-array-comes-back")
        self.assertEqual(gotchas.slug("`InsertCurveFile` is on the document, not the feature manager"),
                         "insertcurvefile-is-on-the-document-not-the")

    def test_json(self):
        data = gotchas.to_json(G)
        self.assertEqual(data["schema"], 1)
        self.assertEqual(list(data["gotchas"][0]), ["number", "id", "title", "always", "members", "languages", "path"])

    def test_fields(self):
        bad = {"id": "G3", "title": "", "always": "yes", "members": ["a.b.c"], "languages": ["all", "csharp"], "x": 1}
        problems = gotchas.check_fields("gotchas/002-x.md", 2, bad)
        self.assertEqual(len(problems), 6, problems)

    def test_languages_in_order(self):
        good = {"id": "G2", "title": "T", "always": False, "members": [], "languages": ["pywin32", "late-bound"]}
        self.assertEqual(gotchas.check_fields("g", 2, good), [])
        problems = gotchas.check_fields("g", 2, dict(good, languages=["late-bound", "pywin32"]))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("in this order", problems[0])

    def test_body_heading_outside_fence(self):
        self.assertEqual(len(gotchas.check_body("g", "Text\n## 3. Not here\n")), 1)
        self.assertEqual(gotchas.check_body("g", G[1]["body"]), [])


if __name__ == "__main__":
    unittest.main()
