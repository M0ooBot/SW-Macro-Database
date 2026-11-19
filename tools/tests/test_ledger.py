import copy
import unittest

import ledger

ROW = {"section": "IModelDoc2", "interface": "IModelDoc2", "members": ["IModelDoc2.SaveAs3"],
       "form": "`SaveAs3(path, 0, 2)`", "purpose": "Save; a | b is a pipe", "on": None,
       "status": "verified", "note": "Verified, SW 2026 (34.0.0)", "provenance": None,
       "languages": [], "majors": [34], "evidence": []}
LEDGER = {"schema": 1, "preamble": "Intro.\n",
          "sections": [{"title": "IModelDoc2", "note": None}, {"title": "Constants", "note": "Free text.\nTwo lines."}],
          "rows": [ROW]}


class LedgerTests(unittest.TestCase):
    def test_render(self):
        self.assertEqual(
            ledger.render_md(LEDGER),
            "# API ledger\n\nIntro.\n\n## IModelDoc2\n\n| Member | Purpose | Status |\n|---|---|---|\n"
            "| `SaveAs3(path, 0, 2)` | Save; a \\| b is a pipe | Verified, SW 2026 (34.0.0) |\n"
            "\n## Constants\n\nFree text.\nTwo lines.\n")

    def test_valid(self):
        self.assertEqual(ledger.check(LEDGER, set()), [])

    def _with(self, **changes):
        bad = copy.deepcopy(LEDGER)
        bad["rows"][0].update(changes)
        return ledger.check(bad, set())

    def test_verified_needs_an_observation(self):
        self.assertEqual(len(self._with(majors=[], note=None)), 1)
        self.assertEqual(self._with(majors=[], note=ledger.NO_VERSION), [])
        self.assertEqual(len(self._with(note=ledger.NO_VERSION)), 1)

    def test_no_version_renders_as_verified(self):
        row = dict(ROW, majors=[], note=ledger.NO_VERSION)
        self.assertEqual(ledger.status_cell(row), "Verified")

    def test_fails_needs_its_wording(self):
        self.assertEqual(len(self._with(status="fails", note=None)), 1)

    def test_bad_values(self):
        self.assertEqual(len(self._with(members=["a.b.c"], interface="Foo", languages=["vba"],
                                        majors=[34, 32], evidence=["nope"], section="X")), 6)


if __name__ == "__main__":
    unittest.main()
