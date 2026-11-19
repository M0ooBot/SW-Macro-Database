import pathlib
import unittest

import recipes

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "recipes"


def check(name):
    return recipes.check((FIXTURES / name).read_text(encoding="utf-8"))


class RecipeHeaderTests(unittest.TestCase):
    def test_good(self):
        header, problems = check("good.csx")
        self.assertEqual(problems, [])
        self.assertEqual(header["effects"], "read-only")
        self.assertEqual(header["params"], [
            {"name": "depth", "type": "number", "required": True, "description": "Extrusion depth in mm."},
            {"name": "name", "type": "string", "required": False, "description": 'Feature name; default "Boss".'},
        ])

    def test_effects_required(self):
        header, problems = check("no-effects.csx")
        self.assertIsNone(header["effects"])
        self.assertEqual(len(problems), 1, problems)

    def test_bad_header(self):
        _, problems = check("bad-header.csx")
        text = "\n".join(problems)
        for expected in ("deletes-everything", "role name", "camelCase", "'decimal'", "'sometimes'",
                         "declared twice", "recipe-colour", "required|optional", "go first"):
            self.assertIn(expected, text)

    def test_undeclared_params(self):
        _, problems = check("undeclared-param.csx")
        self.assertEqual(sorted(problems), sorted([
            "reads ctx.Params 'height', which the header does not declare",
            "reads ctx.Params 'width', which the header does not declare",
        ]))

    def test_crlf(self):
        text = (FIXTURES / "good.csx").read_text(encoding="utf-8").replace("\n", "\r\n")
        self.assertEqual(recipes.check(text)[1], [])


if __name__ == "__main__":
    unittest.main()
