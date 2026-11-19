import json
import pathlib
import unittest

import validate

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = {
    "id": "demo", "title": "Demo", "entry": "entries/files/01-batch-convert-step.md", "status": "unverified",
    "evidence": [], "effects": "edits-open-document", "irreversible": False, "supportsDryRun": True,
    "timeoutMinutes": 5, "openTargets": True,
    "params": [{"name": "targets", "type": "files", "role": "targets", "required": True, "description": "Parts."}],
}
RECORD = {"id": "2026-11-25-demo-cs-34", "subject": "demo", "language": "csharp", "swRevision": "34.1.1",
          "major": 34, "date": "2026-11-25", "method": "smoke", "result": "pass", "scope": "full",
          "observed": "Two parts edited; both reported Modified."}


def check(records=None, **changes):
    data = dict(BASE, **changes)
    return validate.check_script_json(ROOT, "demo", json.dumps(data), records or {})


class ScriptJsonTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(check(), [])

    def test_old_keys_are_refused(self):
        problems = check(verified_on=None)
        self.assertEqual(problems, ["scripts/demo/script.json: unknown key 'verified_on'"])

    def test_edits_open_document_roles(self):
        output = {"name": "out", "type": "folder", "role": "output", "required": True, "description": "Out."}
        self.assertEqual(len(check(params=BASE["params"] + [output])), 1)
        self.assertEqual(len(check(params=[])), 1)

    def test_verified_needs_a_passing_full_record(self):
        self.assertEqual(len(check(status="verified")), 1)
        records = {RECORD["id"]: RECORD}
        self.assertEqual(check(records, status="verified", evidence=[RECORD["id"]]), [])
        partial = {RECORD["id"]: dict(RECORD, scope="partial")}
        self.assertEqual(len(check(partial, status="verified", evidence=[RECORD["id"]])), 1)

    def test_evidence_must_be_about_this_script(self):
        records = {RECORD["id"]: dict(RECORD, subject="other")}
        self.assertEqual(len(check(records, evidence=[RECORD["id"]])), 1)
        self.assertEqual(len(check(evidence=None)), 1)

    def test_open_targets_must_be_a_bool(self):
        self.assertEqual(len(check(openTargets="yes")), 1)


class CsxTests(unittest.TestCase):
    CODE = 'var doc = ctx.Sw.OpenDoc6(path, 1, 1, "", ref e, ref w);\nctx.Sw.CloseDoc(doc.GetTitle());\n'

    def test_direct_open_and_close_refused_with_open_targets(self):
        self.assertEqual(len(validate.check_csx("demo", self.CODE, open_targets=True)), 2)

    def test_allowed_without_open_targets(self):
        self.assertEqual(validate.check_csx("demo", self.CODE, open_targets=False), [])

    def test_close_all_documents_always_refused(self):
        self.assertEqual(len(validate.check_csx("demo", "ctx.Sw.CloseAllDocuments(true);", False)), 1)


if __name__ == "__main__":
    unittest.main()
