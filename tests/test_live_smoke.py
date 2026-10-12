"""No inference required: verify isolated task, contract and non-mutating defaults."""
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import live_smoke as s

class LiveSmokeTests(unittest.TestCase):
    def test_default_preview_never_runs_agent(self):
        for runtime in s.harness.HARNESSES:
            with self.subTest(runtime=runtime):
                r=s.smoke(runtime)
                self.assertEqual(r["status"],"dry-run")
    def test_claude_native_limit_and_fixture_permissions(self):
        p=s.plan("claude",125)
        self.assertIn("--max-budget-usd",p)
        self.assertEqual(p[p.index("--max-budget-usd")+1],"1.25")
        self.assertEqual(p[-2:],["--permission-mode","acceptEdits"])
    def test_hermes_disposable_checkout_no_double_worktree(self):
        p=s.plan("hermes",50)
        self.assertNotIn("--worktree",p)
        self.assertIn("--run-budget",p)
        self.assertNotIn("--yolo",p)
    def test_success_with_mock_agent_writing_correct_proof(self):
        def mock(argv,prompt,root,timeout):
            self.assertIn("proof.txt",prompt)
            self.assertTrue((root/".git").is_dir())
            (root/"proof.txt").write_text(s.PROOF)
            return {"exit_code":0,"stdout":"","stderr":""}
        with patch.object(s.shutil,"which",return_value="/usr/bin/fake"):
            result=s.smoke("codex",execute=True,ack_runtime_permissions=True,runner=mock)
        self.assertEqual(result["status"],"pass")
        self.assertEqual(result["proof_sha256"],result["expected_sha256"])
    def test_incorrect_agent_output_fails(self):
        def wrong(argv,prompt,root,timeout):
            (root/"proof.txt").write_text("AI agent claims everything passed\n")
            return {"exit_code":0}
        with patch.object(s.shutil,"which",return_value="/usr/bin/fake"):
            result=s.smoke("claude",execute=True,ack_runtime_permissions=True,runner=wrong)
        self.assertEqual(result["status"],"failed")
    def test_nonzero_exit_cannot_pass_even_if_proof_exists(self):
        def failed(argv,prompt,root,timeout):
            (root/"proof.txt").write_text(s.PROOF)
            return {"exit_code":12}
        with patch.object(s.shutil,"which",return_value="/usr/bin/fake"):
            result=s.smoke("codex",execute=True,ack_runtime_permissions=True,runner=failed)
        self.assertEqual(result["status"],"failed")
    def test_refuse_paid_without_explicit_permission_ack(self):
        with self.assertRaisesRegex(s.LiveSmokeError,"ack-runtime-permissions"):
            s.smoke("hermes",execute=True)
    def test_reject_invalid_cost_and_runtime(self):
        with self.assertRaises(s.LiveSmokeError):
            s.plan("rogue")
        with self.assertRaises(s.LiveSmokeError):
            s.plan("codex",-1)
if __name__=="__main__":unittest.main()
