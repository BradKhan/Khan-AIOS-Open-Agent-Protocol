"""Real evaluation mechanics and negative cases without model billing."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts import eval_suite as ev

class EvaluationSuiteTests(unittest.TestCase):
    def test_eighteen_unique_tasks_with_held_back_cases(self):
        rows=ev.load()
        self.assertEqual(len(rows),18)
        self.assertGreaterEqual(sum(len(x["cases"]) for x in rows),54)
        self.assertEqual(len({x["id"] for x in rows}),18)
    def test_starter_fails_and_reference_solution_passes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            task=ev.load()[0]
            prompt=ev.prepare(root,task)
            self.assertNotIn("one two three",prompt)
            self.assertFalse(ev.verify(root,task["cases"],backend="unsafe-local")["passed"])
            (root/"solution.py").write_text(
                "def solve(value):\n    return ' '.join(reversed(value.split()))\n")
            self.assertTrue(ev.verify(root,task["cases"],backend="unsafe-local")["passed"])
    def test_agent_workspace_never_receives_validation_cases(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            task=ev.load()[5]
            ev.prepare(root,task,"openass")
            for p in root.rglob("*"):
                if p.is_file():self.assertNotIn('"expected"',p.read_text())
            self.assertTrue((root/"AGENTS.md").is_file())
    def test_compare_matching_records(self):
        base={"suite":"openass-coding-v1","mode":"baseline","harness":"codex",
              "model_version":"test","task_ids":["one"],
              "starter_sha256":"a"*64,
              "results":[{"accepted":False,"elapsed_seconds":1.2,"reported_cost_usd":None}]}
        enhanced=dict(base,mode="openass",results=[
                 {"accepted":True,"elapsed_seconds":1.5,"reported_cost_usd":None}])
        result=ev.compare(base,enhanced)
        self.assertEqual(result["baseline"]["accepted"],0)
        self.assertEqual(result["openass"]["accepted"],1)
        self.assertIsNone(result["openass"]["cost_usd"])
    def test_compare_rejects_different_model(self):
        base={"suite":"x","mode":"baseline","harness":"codex","model_version":"A",
              "task_ids":[],"starter_sha256":"a","results":[]}
        enhanced=dict(base,mode="openass",model_version="B")
        with self.assertRaisesRegex(ev.EvaluationError,"model_version"):
            ev.compare(base,enhanced)
    def test_bad_docker_image_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            ev.prepare(Path(folder),ev.load()[0])
            with self.assertRaises(ev.sandbox.SandboxError):
                ev.verify(Path(folder),ev.load()[0]["cases"],backend="container",image="python:latest")
    def test_manifest_validates_all_cases(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"tasks.json"
            doc={"version":1,"tasks":ev.load()}
            doc["tasks"][1]["id"]=doc["tasks"][0]["id"]
            p.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ev.EvaluationError,"duplicate"):
                ev.load(p)
if __name__=="__main__":
    unittest.main()
