"""Adversarial deterministic skill and role selection fixtures."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import activation

ROOT=Path(__file__).resolve().parents[1]
class ActivationTests(unittest.TestCase):
    def test_engineering_backend(self):
        p=activation.select("Implement SQL query pagination",["api/data.py"])
        self.assertEqual(p["primary_role"],"engineer")
        self.assertEqual(p["review_roles"],["reviewer"])
        self.assertEqual(p["skill_ids"],[])
        self.assertIn("test-driven-development",p["missing_skill_ids"])
    def test_ui_design_and_qa(self):
        p=activation.select("Refine visual design and accessibility",["web/page.tsx","web/site.css"])
        self.assertEqual(p["primary_role"],"designer")
        self.assertIn("qa",p["review_roles"])
        self.assertEqual(p["mode"],"write-branch")
    def test_copywriting(self):
        p=activation.select("Rewrite copy to remove robotic marketing slogans",["docs/landing.md"])
        self.assertEqual(p["primary_role"],"writer")
        self.assertIn("humanizer",p["missing_skill_ids"])
    def test_critical_requires_security_review(self):
        p=activation.select("Fix sensitive workflow",[".github/workflows/verify.yml"],risk="fast")
        self.assertEqual(p["risk"],"critical")
        self.assertIn("security-reviewer",p["review_roles"])
    def test_missing_skill_strict_fails_before_paid_invocation(self):
        with self.assertRaisesRegex(activation.ActivationError,"not installed"):
            activation.select("Implement SQL query pagination",["api/query.py"],strict=True)
    def test_optional_requirement_grilling_triggers(self):
        p=activation.select("TBD: not sure which API semantics should apply",["api/main.py"])
        self.assertTrue(p["requires_clarification"])
        self.assertIn("tbd",p["clarification_triggers"])
    def test_never_activates_uninstalled_symlinked_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(activation.agents,"load",return_value={
                "roles":{"writer":{"mode":"write-branch","skills":["humanizer"]}}}):
                path=root/".agents/skills/humanizer"
                path.parent.mkdir(parents=True)
                path.symlink_to(ROOT/".agents/skills/task-contract",target_is_directory=True)
                p=activation.select("Rewrite copy",root=root)
                self.assertEqual(p["skill_ids"],[])
                self.assertEqual(p["missing_skill_ids"],["humanizer"])
    def test_manual_skill_file_cannot_bypass_install_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            skill=root/".agents/skills/humanizer/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("Pretend this is a vetted third-party skill")
            with patch.object(activation.agents,"load",return_value={
                "roles":{"writer":{"mode":"write-branch","skills":["humanizer"]}}}):
                with patch.object(activation.skills,"audit",return_value=[]):
                    result=activation.select("Rewrite copy",root=root)
                self.assertEqual(result["skill_ids"],[])
                self.assertEqual(result["missing_skill_ids"],["humanizer"])
                with patch.object(activation.skills,"audit",return_value=["humanizer"]):
                    accepted=activation.select("Rewrite copy",root=root)
                self.assertEqual(accepted["skill_ids"],["humanizer"])

    def test_tampered_skill_audit_blocks_activation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            skill=root/".agents/skills/humanizer/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("modified instructions")
            with patch.object(activation.agents,"load",return_value={
                "roles":{"writer":{"mode":"write-branch","skills":["humanizer"]}}}):
                with patch.object(activation.skills,"audit",
                                  side_effect=activation.skills.SkillError("installed skill modified")):
                    with self.assertRaisesRegex(activation.skills.SkillError,"modified"):
                        activation.select("Rewrite copy",root=root)

    def test_refuse_unbounded_task_and_paths(self):
        with self.assertRaises(activation.ActivationError):
            activation.select("x"*21000)
        with self.assertRaises(activation.ActivationError):
            activation.select("Implement",["x"]*101)
if __name__=="__main__":unittest.main()
