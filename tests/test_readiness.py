"""Read-only readiness report tests."""
import unittest
from scripts import readiness
class ReadinessTests(unittest.TestCase):
    def test_missing_owner_controls(self):
        r=readiness.evaluate({"is_template":False,"topics":[]},{"protected":False})
        self.assertFalse(r["ready"])
        self.assertEqual(len(r["owner_actions"]),3)
    def test_configured_flags(self):
        r=readiness.evaluate({"is_template":True,"topics":["ai-agents"]},{"protected":True})
        self.assertTrue(r["ready"])
        self.assertIn("does not attest",r["warning"])
    def test_missing_metadata_fails(self):
        with self.assertRaises(readiness.ReadinessError):
            readiness.evaluate(None,None)
if __name__=="__main__":unittest.main()
