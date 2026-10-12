"""Bootstrap/role regression tests; never runs supplied app commands."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts import project_setup, role_sync
ROOT=Path(__file__).resolve().parents[1]
class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.ctx=tempfile.TemporaryDirectory()
        self.root=Path(self.ctx.name)
        (self.root/"config").mkdir();(self.root/".github").mkdir()
        (self.root/"config/project.json").write_text(json.dumps({"initialized":False,"verification":{}}))
        (self.root/".github/CODEOWNERS").write_text("* @BradKhan\n")
    def tearDown(self):self.ctx.cleanup()
    def test_dry_run_does_not_mutate(self):
        changes=project_setup.build(self.root,"Project","OtherOwner","standard",["npm","test"])
        self.assertIn("@BradKhan",(self.root/".github/CODEOWNERS").read_text())
        self.assertNotIn("@BradKhan",changes[self.root/".github/CODEOWNERS"])
        project_setup.apply(changes)
        self.assertIn("@OtherOwner",(self.root/".github/CODEOWNERS").read_text())
    def test_cannot_reinitialize(self):
        project_setup.apply(project_setup.build(self.root,"Project","owner","standard",["pytest"]))
        with self.assertRaisesRegex(project_setup.SetupError,"already initialized"):
            project_setup.build(self.root,"Another","owner","standard",["pytest"])
    def test_reject_invalid_owner(self):
        for candidate in ("a/b","../x","@owner","a--b"):
            with self.subTest(candidate=candidate),self.assertRaises(project_setup.SetupError):
                project_setup.build(self.root,"Project",candidate,"standard",["pytest"])
    def test_critical_requires_security(self):
        with self.assertRaisesRegex(project_setup.SetupError,"security"):
            project_setup.build(self.root,"Project","owner","critical",["pytest"])
    def test_app_command_not_executed(self):
        marker=self.root/"unexpected"
        project_setup.apply(project_setup.build(self.root,"Project","owner","standard",["touch",str(marker)]))
        self.assertFalse(marker.exists())
    def test_reject_symlink(self):
        path=self.root/"config/project.json";path.unlink()
        path.symlink_to(self.root/".github/CODEOWNERS")
        with self.assertRaisesRegex(project_setup.SetupError,"symlinked"):
            project_setup.build(self.root,"Project","owner","standard",["pytest"])
class RoleTests(unittest.TestCase):
    def test_generated_files_match_registry(self):
        self.assertEqual(role_sync.synchronize(ROOT),9)
    def test_read_only_reviewer_tools(self):
        roles=json.loads((ROOT/"config/agents.json").read_text())["roles"]
        self.assertIn("tools: Read, Grep, Glob\n",role_sync.render("reviewer",roles["reviewer"]))
        self.assertNotIn("Write, Bash",role_sync.render("reviewer",roles["reviewer"]))
    def test_role_drift_detection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"config").mkdir();(root/"integrations").mkdir()
            (root/"config/agents.json").write_text((ROOT/"config/agents.json").read_text())
            (root/"integrations/skills.lock.json").write_text((ROOT/"integrations/skills.lock.json").read_text())
            role_sync.synchronize(root,write=True)
            p=root/".claude/agents/reviewer.md";p.write_text(p.read_text()+"injected\n")
            with self.assertRaisesRegex(ValueError,"drifted"):
                role_sync.synchronize(root)
if __name__=="__main__":unittest.main()
