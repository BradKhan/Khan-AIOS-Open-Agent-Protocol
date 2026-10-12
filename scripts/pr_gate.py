#!/usr/bin/env python3
"""CI PR risk declaration and sensitive-file escalation.

GitHub branch rulesets MUST independently enforce checks/review/merge rights.
A PR author can edit their PR body; this is a gate, not authorization.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANK = {"fast": 0, "standard": 1, "critical": 2}
SENSITIVE = (".github/workflows/", "config/", ".mcp.json", ".codex/",
             "POLICY.md", "SECURITY.md", "scripts/pr_gate.py",
             "scripts/security_baseline.py", "scripts/verify.py",
             "scripts/skills.py", "scripts/mcp_server.py", "scripts/hook_gate.py")
CODE = ("scripts/", "tests/", ".agents/", "contracts/", "context/")
RISK = re.compile(r"(?im)^\s*Risk(?: class)?\s*:\s*(fast|standard|critical)\s*$")
ISSUE = re.compile(r"(?im)^\s*Issue\s*:\s*(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#([1-9][0-9]*)\s*$")


class GateError(ValueError):
    pass


def required_risk(paths):
    if not isinstance(paths, list) or not paths:
        raise GateError("cannot determine PR changes")
    minimum = "fast"
    for path in paths:
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in path.split("/"):
            raise GateError("unsafe PR path")
        if path.startswith(SENSITIVE) or re.search(r"(^|/)(auth|payment|permissions|secrets|credentials)(/|[._-])", path, re.I):
            return "critical"
        if path.startswith(CODE) or path in ("AGENTS.md", "ARCHITECTURE.md", "justfile"):
            minimum = "standard"
    return minimum


def check(body, changed, initialized=False, security_command=None):
    if not isinstance(body, str):
        raise GateError("missing PR body")
    risks = RISK.findall(body)
    links = ISSUE.findall(body)
    if len(risks) != 1 or len(links) != 1:
        raise GateError("PR must contain one 'Risk: fast|standard|critical' and one 'Issue: #number'")
    risk = risks[0].lower()
    required = required_risk(changed)
    if RANK[risk] < RANK[required]:
        raise GateError("declared risk " + risk + " is below required " + required)
    if initialized and risk == "critical" and not security_command:
        raise GateError("critical application PR requires configured application security checks")
    if not re.search(r"(?im)^\s*Verification\s*:", body):
        raise GateError("PR needs a Verification: line with reproducible evidence")
    if risk == "critical" and not re.search(r"(?im)^\s*Security review\s*:", body):
        raise GateError("critical PR needs Security review: independent reviewer/evidence")
    return {"issue": int(links[0]), "declared": risk, "minimum": required, "paths": len(changed),
            "note": "PR metadata validation is not independent approval."}


def git_changes(base, head):
    if not all(isinstance(s, str) and re.fullmatch("[a-f0-9]{40}", s) for s in (base, head)):
        raise GateError("invalid PR Git revisions")
    cmd = ["git", "diff", "--name-only", "-z", base + "..." + head]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    if p.returncode:
        raise GateError("cannot determine PR changed files: " + p.stderr.decode(errors="replace")[:200])
    return [x.decode() for x in p.stdout.split(b"\x00") if x]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--event", required=True, help="GitHub pull_request event JSON")
    p.add_argument("--changed", action="append", default=[], help="Test override; do not use in protected CI")
    a = p.parse_args()
    try:
        event = json.loads(Path(a.event).read_text())
        pull = event.get("pull_request")
        if not isinstance(pull, dict):
            raise GateError("not a pull_request event")
        changed = a.changed or git_changes(pull["base"]["sha"], pull["head"]["sha"])
        config = json.loads((ROOT / "config/project.json").read_text())
        settings = config.get("verification", {})
        result = check(pull.get("body"), changed,
                       config.get("initialized") is True,
                       settings.get("security_command"))
        print(json.dumps(result, indent=2))
    except (GateError, OSError, KeyError, ValueError, TypeError) as exc:
        print("pr-gate: " + str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
