"""Release-train policy: one validated contract drives admin rules and attestation."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts import release_policy, attest, github_admin

ROOT=Path(__file__).resolve().parents[1]

class ReleaseContractTests(unittest.TestCase):
    def test_live_policy_drives_both_trust_boundaries(self):
        p=release_policy.read()
        self.assertEqual(set(attest.DEFAULT_REQUIRED),set(p["checks"]))
        self.assertEqual(set(github_admin.CHECKS),set(p["checks"]))
        self.assertEqual(github_admin.GH_ACTIONS_APP_ID,p["app_id"])
        self.assertIn("harness-cli",p["checks"])
        self.assertIn("browser-fixtures",p["checks"])

    def make_fixture(self,edit=None):
        tmp=tempfile.TemporaryDirectory()
        root=Path(tmp.name)
        (root/"config").mkdir()
        for entry in json.loads(release_policy.POLICY.read_text())["checks"]:
            source=ROOT/entry["workflow"]
            target=root/entry["workflow"]
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(source.read_text())
        doc=json.loads(release_policy.POLICY.read_text())
        if edit:edit(doc)
        path=root/"config/release-gates.json"
        path.write_text(json.dumps(doc))
        return tmp,root,path

    def test_duplicate_required_check_refused(self):
        def mutate(d):d["checks"].append(dict(d["checks"][0]))
        tmp,root,path=self.make_fixture(mutate)
        try:
            with self.assertRaisesRegex(release_policy.ReleasePolicyError,"duplicate"):
                release_policy.read(path,root)
        finally:tmp.cleanup()

    def test_bad_job_name_refused(self):
        def mutate(d):d["checks"][0]["job"]="non-existent"
        tmp,root,path=self.make_fixture(mutate)
        try:
            with self.assertRaises(release_policy.ReleasePolicyError):
                release_policy.read(path,root)
        finally:tmp.cleanup()

    def test_missing_workflow_refused(self):
        tmp,root,path=self.make_fixture()
        try:
            (root/".github/workflows/verify.yml").unlink()
            with self.assertRaisesRegex(release_policy.ReleasePolicyError,"missing"):
                release_policy.read(path,root)
        finally:tmp.cleanup()

    def test_pr_path_filter_refused(self):
        tmp,root,path=self.make_fixture()
        try:
            file=root/".github/workflows/verify.yml"
            original = file.read_text()
            data = original.replace("  pull_request:", "  pull_request:" + chr(10)
                                    + "    paths:" + chr(10) + "      - 'src/**'")
            self.assertNotEqual(original, data, "test fixture did not inject path filter")
            file.write_text(data)
            with self.assertRaisesRegex(release_policy.ReleasePolicyError,"path-filtered"):
                release_policy.read(path,root)
        finally:tmp.cleanup()

    def test_wrong_matrix_version_refused(self):
        tmp,root,path=self.make_fixture()
        try:
            p=root/".github/workflows/quality.yml"
            p.write_text(p.read_text().replace("'3.13'","'3.14'"))
            with self.assertRaisesRegex(release_policy.ReleasePolicyError,"matrix version"):
                release_policy.read(path,root)
        finally:tmp.cleanup()

if __name__=="__main__":
    unittest.main()
