"""Contract probes do not execute inference, only --help and --version."""
import subprocess
import unittest
from scripts import harness_compat as h

def faked(args,text=True,capture_output=True,timeout=20,check=False):
    if "--version" in args:
        return subprocess.CompletedProcess(args,0,"2.1.296", "")
    return subprocess.CompletedProcess(args,0," ".join(h.FLAGS[args[0]][1]),"")

class CompatTests(unittest.TestCase):
    def test_all_fake_clis_checked(self):
        for name in h.FLAGS:
            with self.subTest(name=name):
                self.assertEqual(h.probe(name,runner=faked,locator=lambda x:x)["status"],"pass")
    def test_claude_hidden_turn_limit_does_not_fail_help_probe(self):
        self.assertNotIn("--max-turns",h.FLAGS["claude"][1])
        from scripts import harness
        self.assertIn("--max-turns",harness.command("claude","write-branch"))

    def test_absent_flags_rejected(self):
        def missing(args,**kw):return subprocess.CompletedProcess(args,0,"--help","")
        self.assertEqual(h.probe("hermes",runner=missing,locator=lambda n:n)["status"],"incompatible")
    def test_no_binary_is_explicit(self):
        self.assertEqual(h.probe("codex",locator=lambda n:None)["status"],"missing")
    def test_version_checked(self):
        self.assertEqual(h.probe("claude",runner=faked,locator=lambda n:n,
                                 expected_version="2.1.296")["status"],"pass")
        self.assertEqual(h.probe("claude",runner=faked,locator=lambda n:n,
                                 expected_version="3.0.0")["status"],"incompatible")

if __name__=="__main__":
    unittest.main()
