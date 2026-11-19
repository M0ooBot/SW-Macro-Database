import unittest

from frontmatter import format_value, parse_value, read_frontmatter


class FrontmatterTests(unittest.TestCase):
    def test_values(self):
        fm, problems = read_frontmatter(
            '---\nschema: 2\ntitle: "\\"Quoted\\" start"\nalways: false\nmajors: [32, 34]\n'
            'recipe_status: null\nlanguage: []\n---\nbody\n')
        self.assertEqual(problems, [])
        self.assertEqual(fm, {"schema": "2", "title": '"Quoted" start', "always": False,
                              "majors": ["32", "34"], "recipe_status": None, "language": []})

    def test_unreadable_line_and_repeated_key_are_problems(self):
        fm, problems = read_frontmatter("---\nid: a\n- item\nid: b\n---\n")
        self.assertEqual(fm, {"id": "a"})
        self.assertEqual(len(problems), 2)

    def test_no_block(self):
        self.assertEqual(read_frontmatter("# Title\n"), (None, []))

    def test_format_round_trips(self):
        for v in ["plain text", '"quoted" start', "ends in 'quote'", "true", "null", "[bracket",
                  "back\\slash and \"quote\"", None, True, False, 2, [], ["a", "B.c"]]:
            self.assertEqual(parse_value(format_value(v)), v if not isinstance(v, int) or isinstance(v, bool) else str(v))

    def test_format_refuses_what_it_cannot_write(self):
        with self.assertRaises(ValueError):
            format_value(["a, b"])
        with self.assertRaises(ValueError):
            format_value("two\nlines")


if __name__ == "__main__":
    unittest.main()
