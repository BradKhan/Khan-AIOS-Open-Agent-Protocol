"""Contract tests for three real CLI shapes and opt-in subprocess execution."""
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
from scripts import harness, agents
ROOT=Path(__file__).resolve().parents[1]
class HarnessTests(unittest.TestCase):
    def test_all_three_modes_and_harnesses(self):
        for runtime in harness.HARNESSES:
            for mode in ("read","write-branch"):
                with self.subTest(runtime=runtime,mode=mode):
                    argv=harness.command(runtime,mode)
                    self.assertEqual(argv[0],runtime)
                    self.assertNotIn("--dangerously-skip-permissions",argv)
                    self.assertNotIn("--yolo",argv)
    def test_codex_read_only_and_write_sandbox(self):
        self.assertIn("read-only",harness.command("codex","read"))
        self.assertIn("workspace-write",harness.command("codex","write-branch"))
    def test_hermes_noninteractive_and_safe_mode(self):
        self.assertIn("--query-file",harness.command("hermes","read"))
        self.assertIn("--safe-mode",harness.command("hermes","read"))
        self.assertIn("--worktree",harness.command("hermes","write-branch"))
    def test_claude_plan_mode_for_reviewers(self):
        self.assertIn("plan",harness.command("claude","read"))
    def test_handoff_provenance(self):
        p=harness.make_prompt("reviewer",root=ROOT)
        self.assertIn('"role": "reviewer"',p)
        self.assertIn('"sha256":',p)
        self.assertIn("Do not self-approve",p)
    def test_actual_fake_process_receives_input_without_shell(self):
        done=subprocess.CompletedProcess(["codex"],0,stdout="OK",stderr="")
        mock=Mock(return_value=done)
        result=harness.execute(["codex","exec","-"],"instruction",runner=mock)
        self.assertEqual(result["exit_code"],0)
        kwargs=mock.call_args.kwargs
        self.assertEqual(kwargs["input"],"instruction")
        self.assertFalse(kwargs["check"])
        self.assertNotIn("shell",kwargs)
    def test_timeout_failure(self):
        def timed_out(*a,**kw):raise subprocess.TimeoutExpired(a[0],1)
        with self.assertRaises(harness.HarnessError):
            harness.execute(["claude","-p"],"input",runner=timed_out)
    def test_invalid_runtime_and_mode(self):
        with self.assertRaises(harness.HarnessError):
            harness.command("shell","read")
        with self.assertRaises(harness.HarnessError):
            harness.execute(["bash","-c","echo x"],"p")
    def test_output_bounded(self):
        result=harness.execute(["codex","exec"],"input",
            runner=Mock(return_value=subprocess.CompletedProcess([],0,"x"*100005,"y"*20005)))
        self.assertEqual(len(result["stdout"]),100000)
        self.assertTrue(result["truncated"])
if __name__=="__main__":unittest.main()
