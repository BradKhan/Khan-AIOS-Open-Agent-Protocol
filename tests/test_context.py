"""Deterministic tests for ICM stage routing and context manifest boundaries."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts import context


class ContextTests(unittest.TestCase):
    def test_routes_validate(self):
        routes = context.validate()
        self.assertTrue(context.MANDATORY_STAGES.issubset(routes["stages"]))

    def test_stage_manifest_scoped_and_hashed(self):
        item = context.plan("implement", ["examples/task.json"])
        files = item["files"]
        names = {x["path"] for x in files}
        self.assertIn("AGENTS.md", names)
        self.assertIn("CONTEXT.md", names)
        self.assertIn("examples/task.json", names)
        self.assertNotIn("context/stages/research/CONTEXT.md", names)
        self.assertTrue(all(len(x["sha256"]) == 64 for x in files))
        self.assertEqual(item, context.plan("implement", ["examples/task.json"]))

    def test_rejects_path_escape(self):
        for path in ("../outside.txt", "/etc/passwd", "a/../../secret", r"a\\b"):
            with self.subTest(path=path), self.assertRaises(context.ContextError):
                context.confined_file(context.ROOT, path)

    def test_unknown_stage(self):
        with self.assertRaisesRegex(context.ContextError, "unknown stage"):
            context.plan("everything")

    def test_rejects_missing_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "AGENTS.md").write_text("Agent entry")
            (root / "CONTEXT.md").write_text("Router")
            (root / "context").mkdir()
            data = {"version": "0.1", "stages": {}}
            (root / "context/routes.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(context.ContextError, "missing required ICM stage"):
                context.validate(root)

    def test_rejects_duplicate_working_file(self):
        with self.assertRaisesRegex(context.ContextError, "duplicate loaded context"):
            context.plan("implement", ["PROJECT.md"])

    def test_missing_required_stage_contract_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("Entry")
            (root / "CONTEXT.md").write_text("Router")
            (root / "context/stages").mkdir(parents=True)
            stages = {}
            for name in context.MANDATORY_STAGES:
                route = "context/stages/" + name + "/CONTEXT.md"
                path = root / route
                path.parent.mkdir(parents=True)
                path.write_text("## Inputs\n- A\n## Process\n- B\n## Outputs\n- C\n## References\n- D\n")
                stages[name] = {"context": route, "references": ["AGENT_POLICY.md"]}
            (root / "AGENT_POLICY.md").write_text("policy")
            (root / "context/routes.json").write_text(json.dumps({"version": "0.1", "stages": stages}))
            with self.assertRaisesRegex(context.ContextError, "ordered contract sections"):
                context.validate(root)


if __name__ == "__main__":
    unittest.main()
