"""Hermetic tests of MCP, role routing, PR gates and local security checks."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import agents, context, mcp_server, pr_gate, security_baseline, openass

ROOT = Path(__file__).resolve().parents[1]


class RoleTests(unittest.TestCase):
    def test_real_roles_valid(self):
        self.assertGreaterEqual(len(agents.load()["roles"]), 9)

    def test_engineer_role_and_context_are_bounded(self):
        p = agents.plan("engineer", ["examples/task.json"])
        self.assertEqual(p["stage"], "implement")
        self.assertEqual(p["mode"], "write-branch")
        self.assertIn("examples/task.json", [x["path"] for x in p["context"]["files"]])
        self.assertNotIn("context/stages/research/CONTEXT.md", [x["path"] for x in p["context"]["files"]])

    def test_reviewer_is_read_only(self):
        self.assertEqual(agents.plan("reviewer")["mode"], "read")
        self.assertEqual(agents.plan("security-reviewer")["mode"], "read")

    def test_context_bundle_contains_real_hashed_text(self):
        import hashlib
        b = agents.bundle("engineer", ["examples/task.json"], max_bytes=100000)
        self.assertEqual(b["role"], "engineer")
        self.assertGreater(b["bytes"], 0)
        self.assertTrue(any(s["path"] == "AGENTS.md" for s in b["sources"]))
        self.assertEqual(b, agents.bundle("engineer", ["examples/task.json"], max_bytes=100000))
        self.assertTrue(all(hashlib.sha256(s["text"].encode()).hexdigest() == s["sha256"] for s in b["sources"]))

    def test_context_bundle_budget_rejects_excess(self):
        with self.assertRaisesRegex(agents.AgentError, "byte budget"):
            agents.bundle("engineer", max_bytes=10)

    def test_context_bundle_rejects_skill_outside_role(self):
        with self.assertRaisesRegex(agents.AgentError, "not declared"):
            agents.bundle("engineer", include_skills=["impeccable"])

    def test_context_bundle_requires_installed_skill(self):
        with self.assertRaisesRegex(agents.AgentError, "not installed"):
            agents.bundle("designer", include_skills=["impeccable"])

    def test_unknown_role_rejected(self):
        with self.assertRaises(agents.AgentError):
            agents.plan("root-admin")

    def test_writable_review_role_rejected(self):
        document = json.loads((ROOT / "config/agents.json").read_text())
        document["roles"]["reviewer"]["mode"] = "write-branch"
        from scripts import skills
        with self.assertRaises(agents.AgentError):
            agents.validate(document, skills.load())


class MCPTests(unittest.TestCase):
    def test_initialize(self):
        r = mcp_server.dispatch({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}})
        self.assertEqual(r["result"]["capabilities"]["tools"], {"listChanged": False})

    def test_tools_are_read_only_and_well_formed(self):
        tools = mcp_server.dispatch({"jsonrpc":"2.0","id":1,"method":"tools/list"})["result"]["tools"]
        names = {t["name"] for t in tools}
        self.assertEqual(names, {"openass_context_plan", "openass_agent_plan", "openass_skill_profiles"})
        self.assertTrue(all(t["inputSchema"].get("additionalProperties") is False for t in tools))

    def test_context_plan(self):
        r = mcp_server.dispatch({"jsonrpc":"2.0","id":2,"method":"tools/call",
                                 "params":{"name":"openass_context_plan","arguments":{"stage":"implement"}}})
        content = json.loads(r["result"]["content"][0]["text"])
        self.assertEqual(content["stage"], "implement")

    def test_agent_plan(self):
        r = mcp_server.dispatch({"jsonrpc":"2.0","id":3,"method":"tools/call",
                                 "params":{"name":"openass_agent_plan","arguments":{"role":"reviewer"}}})
        self.assertEqual(json.loads(r["result"]["content"][0]["text"])["mode"],"read")

    def test_path_escape_cannot_read_secrets(self):
        r = mcp_server.dispatch({"jsonrpc":"2.0","id":4,"method":"tools/call",
                                 "params":{"name":"openass_context_plan","arguments":{"stage":"implement","working":["../../etc/passwd"]}}})
        self.assertIn("error", r)

    def test_unsupported_tool_and_argument(self):
        r = mcp_server.dispatch({"jsonrpc":"2.0","id":1,"method":"tools/call",
                                 "params":{"name":"execute_shell","arguments":{}}})
        self.assertTrue(r["result"]["isError"])
        r = mcp_server.dispatch({"jsonrpc":"2.0","id":1,"method":"tools/call",
                                 "params":{"name":"openass_skill_profiles","arguments":{"shell":"rm"}}})
        self.assertIn("error",r)

    def test_notifications_have_no_response(self):
        self.assertIsNone(mcp_server.dispatch({"jsonrpc":"2.0","method":"notifications/initialized"}))

    def test_stdio_transport(self):
        request = ('{"jsonrpc":"2.0","id":1,"method":"initialize"}\n'
                   '{"jsonrpc":"2.0","method":"notifications/initialized"}\n'
                   '{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n')
        out = io.StringIO()
        mcp_server.serve(io.StringIO(request), out)
        responses = [json.loads(x) for x in out.getvalue().splitlines()]
        self.assertEqual(len(responses),2)
        self.assertEqual(responses[0]["id"],1)

    def test_invalid_json_returns_error(self):
        out=io.StringIO()
        mcp_server.serve(io.StringIO("{oops\n"),out)
        self.assertEqual(json.loads(out.getvalue())["error"]["code"],-32700)


class PullRequestGateTests(unittest.TestCase):
    def test_clean_fast_docs(self):
        result=pr_gate.check("Issue: #13\nRisk: fast\nVerification: markdown links checked", ["docs/foo.md"])
        self.assertEqual(result["declared"], "fast")

    def test_critical_escalation(self):
        with self.assertRaisesRegex(pr_gate.GateError,"below required"):
            pr_gate.check("Issue: #13\nRisk: standard\nVerification: tests", ["scripts/verify.py"])

    def test_critical_needs_review_marker(self):
        with self.assertRaisesRegex(pr_gate.GateError,"Security review"):
            pr_gate.check("Issue: #13\nRisk: critical\nVerification: tests", ["scripts/verify.py"])

    def test_critical_valid_when_declared(self):
        result=pr_gate.check("Issue: #13\nRisk: critical\nVerification: tests\nSecurity review: requested",
                             ["scripts/verify.py"])
        self.assertEqual(result["minimum"], "critical")

    def test_initialized_critical_needs_security_command(self):
        with self.assertRaisesRegex(pr_gate.GateError,"security checks"):
            pr_gate.check("Issue: #13\nRisk: critical\nVerification: tests\nSecurity review: requested",
                          ["src/auth/token.py"], initialized=True, security_command=None)

    def test_missing_issue_and_duplicate_risks(self):
        for body in ("Risk: standard\nVerification: tests",
                     "Issue: #13\nRisk: standard\nRisk: fast\nVerification: tests"):
            with self.assertRaises(pr_gate.GateError):
                pr_gate.check(body, ["src/app.py"])

    def test_reject_empty_changes(self):
        with self.assertRaises(pr_gate.GateError):
            pr_gate.required_risk([])

    def test_security_sensitive_path_requires_critical(self):
        self.assertEqual(pr_gate.required_risk([".github/workflows/test.yml"]), "critical")
        self.assertEqual(pr_gate.required_risk(["src/auth/session.py"]), "critical")


class FrameworkSecurityTests(unittest.TestCase):
    def test_live_framework_security_baseline(self):
        self.assertTrue(security_baseline.check())

    def test_unpinned_action_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"scripts").mkdir()
            (root/".github/workflows").mkdir(parents=True)
            (root/".github/workflows/unsafe.yml").write_text(
                "name: unsafe\non: [push]\npermissions:\n  contents: read\njobs:\n  x:\n    steps:\n      - uses: actions/checkout@main\n")
            with self.assertRaises(security_baseline.SecurityError):
                security_baseline.check(root)

    def test_privileged_trigger_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"scripts").mkdir()
            (root/".github/workflows").mkdir(parents=True)
            (root/".github/workflows/unsafe.yml").write_text(
                "on:\n  pull_request_target:\npermissions:\n  contents: read\n")
            with self.assertRaises(security_baseline.SecurityError):
                security_baseline.check(root)

    def test_shell_true_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"scripts").mkdir()
            (root/"scripts/unsafe.py").write_text("import subprocess\nsubprocess.run('echo hi',shell=True)\n")
            (root/".github/workflows").mkdir(parents=True)
            with self.assertRaises(security_baseline.SecurityError):
                security_baseline.check(root)


class HookTests(unittest.TestCase):
    def test_local_hooks_install_and_uninstall(self):
        if not shutil_available("git"):
            self.skipTest("Git unavailable")
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            subprocess.run(["git","init","-q"],cwd=root,check=True)
            with patch.object(openass,"ROOT",root):
                self.assertEqual(openass.hook("install"),0)
                p=subprocess.run(["git","config","--local","--get","core.hooksPath"],
                                 cwd=root,text=True,capture_output=True)
                self.assertEqual(p.stdout.strip(),".githooks")
                self.assertEqual(openass.hook("uninstall"),0)

    def test_existing_hooks_cannot_be_overwritten(self):
        if not shutil_available("git"):
            self.skipTest("Git unavailable")
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            subprocess.run(["git","init","-q"],cwd=root,check=True)
            subprocess.run(["git","config","--local","core.hooksPath","custom-hooks"],cwd=root,check=True)
            with patch.object(openass,"ROOT",root):
                with self.assertRaises(RuntimeError):
                    openass.hook("install")


def shutil_available(name):
    import shutil
    return bool(shutil.which(name))


if __name__ == "__main__":
    unittest.main()
