import unittest

import evidence

GOOD = {"id": "2026-11-25-sketches-04-cs-32", "subject": "sketches-04-dimensions", "language": "csharp",
        "swRevision": "32.5.0", "major": 32, "date": "2026-11-25", "method": "smoke", "result": "pass",
        "scope": "full", "observed": "Closed profile of 4 lines on Front Plane; sketch fully defined."}


class EvidenceTests(unittest.TestCase):
    def test_good(self):
        self.assertEqual(evidence.check_record("e", GOOD["id"], GOOD), [])

    def test_bad(self):
        bad = dict(GOOD, id="Bad_Id", language="csharp-script", swRevision="33.0.0", date="2026-13-01",
                   method="guess", result="maybe", scope="most", extra=1)
        problems = evidence.check_record("e", "other", bad)
        self.assertEqual(len(problems), 8, problems)

    def test_private_text(self):
        for text in (r"Saved C:\Users\me\part.sldprt", "read /mnt/c/x", "opened Bracket.SLDPRT", r"\\server\share"):
            problems = evidence.check_record("e", GOOD["id"], dict(GOOD, observed=text))
            self.assertTrue(problems, text)

    def test_helpers(self):
        records = {GOOD["id"]: GOOD, "x": dict(GOOD, id="x", result="fail", major=34)}
        self.assertTrue(evidence.has_full_pass([GOOD["id"]], records, method="smoke"))
        self.assertFalse(evidence.has_full_pass(["x"], records))
        self.assertEqual(evidence.passing_majors([GOOD["id"], "x"], records), {32})
        problems = []
        evidence.check_refs("e", "evidence", [GOOD["id"], "missing"], "other-entry", records, problems, language="python")
        self.assertEqual(len(problems), 3, problems)


if __name__ == "__main__":
    unittest.main()
