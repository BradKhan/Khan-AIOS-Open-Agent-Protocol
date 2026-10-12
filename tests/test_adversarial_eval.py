"""Adversarial evaluation suite includes negative controls."""
import unittest
from scripts import adversarial_eval as ev
class EvaluationTests(unittest.TestCase):
    def test_all_failure_injection_cases(self):
        report=ev.evaluate()
        self.assertEqual(report["passed"],len(ev.CASES),report)
    def test_reject_unknown_case(self):
        with self.assertRaises(ev.EvaluationError):
            ev.evaluate(["unlisted"])
    def test_reject_duplicate_case(self):
        with self.assertRaises(ev.EvaluationError):
            ev.evaluate(["pr-risk","pr-risk"])
    def test_each_case_returns_observed_boolean(self):
        for name in ev.CASES:
            with self.subTest(name=name):
                self.assertIs(ev.run(name),True)
if __name__=="__main__":unittest.main()
