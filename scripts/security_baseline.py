#!/usr/bin/env python3
"""Deterministic, dependency-free checks for the Open ASS framework itself.

Not a vulnerability scanner for downstream applications.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecurityError(ValueError):
    pass


def check(root=ROOT):
    scripts = root / "scripts"
    for path in sorted(scripts.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        raise SecurityError("shell=True in framework: " + str(path))
                if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                    raise SecurityError("dynamic Python execution: " + str(path))
    workflows = root / ".github" / "workflows"
    for path in sorted(workflows.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if "workflow_run:" in text:
            raise SecurityError("unsafe workflow-run trigger: " + path.name)
        if "pull_request_target:" in text:
            raise SecurityError("privileged PR trigger forbidden: " + path.name)
        if not re.search(r"(?m)^permissions:\s*\n\s+contents:\s*read\s*$", text):
            raise SecurityError("workflow needs top-level least-privilege permissions: " + path.name)
        for match in re.findall(r"(?m)^\s*-\s*(?:name:.*\n\s+)?uses:\s*(\S+)", text):
            if not re.search(r"@[0-9a-f]{40}$", match):
                raise SecurityError("unpinned GitHub action: " + match)
        if re.search(r"(?i)(curl|wget)\b[^\n|]*\|\s*(?:bash|sh)\b", text):
            raise SecurityError("download-pipe-shell workflow: " + path.name)
    return True


if __name__ == "__main__":
    try:
        check()
        print("Framework static security baseline PASS; application security not covered")
    except (SecurityError, SyntaxError, OSError) as exc:
        print("security-baseline: " + str(exc), file=sys.stderr)
        sys.exit(1)
