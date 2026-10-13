"""Executable CLI import regression: run dispatcher outside package execution."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class DispatchCLITests(unittest.TestCase):
    def test_direct_script_help(self):
        run=subprocess.run([sys.executable, str(ROOT/"scripts/dispatch.py"), "--help"],
                           cwd=ROOT,capture_output=True,text=True,timeout=15,check=False)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertIn("--strict-skills",run.stdout)

    def test_activation_import_is_available(self):
        from scripts import dispatch
        self.assertTrue(callable(dispatch.activation.select))

if __name__=="__main__":
    unittest.main()
