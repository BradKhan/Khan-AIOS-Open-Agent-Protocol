#!/usr/bin/env python3
"""Opt-in local hooks. Git hooks are convenience checks, never authoritative gates."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*arguments):
    p = subprocess.run([sys.executable, *arguments], cwd=ROOT, check=False)
    if p.returncode:
        raise SystemExit(p.returncode)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("pre-commit", "pre-push"):
        raise SystemExit("usage: hook_gate.py pre-commit|pre-push")
    run("scripts/context.py", "check")
    run("scripts/skills.py", "check")
    run("scripts/agents.py", "check")
    run("scripts/security_baseline.py")
    if sys.argv[1] == "pre-push":
        run("scripts/verify.py")
    print("Open ASS " + sys.argv[1] + " checks passed")


if __name__ == "__main__":
    main()
