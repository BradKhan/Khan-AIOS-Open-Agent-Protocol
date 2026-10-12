#!/usr/bin/env python3
"""Bounded agent role definitions and inspectable context/skill handoffs."""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from scripts import context, skills
except ModuleNotFoundError:
    import context, skills

ROOT = Path(__file__).resolve().parents[1]
ROLE_FILE = "config/agents.json"
NAME = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
STAGES = {"research", "specify", "implement", "verify", "release"}
MODES = {"read", "write-branch"}


class AgentError(ValueError):
    pass


def load(root=ROOT):
    document = json.loads((root / ROLE_FILE).read_text(encoding="utf-8"))
    validate(document, skills.load(root))
    return document


def validate(document, catalog):
    if not isinstance(document, dict) or document.get("version") != 1 or not isinstance(document.get("roles"), dict):
        raise AgentError("invalid role registry")
    defined = {skill["id"] for skill in catalog["skills"]}
    for name, role in document["roles"].items():
        if not NAME.fullmatch(name) or not isinstance(role, dict):
            raise AgentError("invalid role name or record")
        if role.get("stage") not in STAGES or role.get("mode") not in MODES:
            raise AgentError("invalid role stage or mode: " + name)
        if role["mode"] == "write-branch" and role["stage"] != "implement":
            raise AgentError("write role outside implementation: " + name)
        entries = role.get("skills")
        if not isinstance(entries, list) or len(set(entries)) != len(entries) or any(s not in defined for s in entries):
            raise AgentError("missing or repeated role skill: " + name)
        for field in ("purpose", "handoff"):
            if not isinstance(role.get(field), str) or not role[field].strip():
                raise AgentError("missing role " + field + ": " + name)
    if not {"engineer", "reviewer", "security-reviewer", "qa"} <= set(document["roles"]):
        raise AgentError("mandatory roles missing")
    return True


def plan(role_name, working=None, root=ROOT):
    roles = load(root)["roles"]
    if role_name not in roles:
        raise AgentError("unknown role: " + role_name)
    role = roles[role_name]
    context_files = context.plan(role["stage"], working or [], root)
    available = []
    for sid in role["skills"]:
        directory = root / ".agents" / "skills" / sid
        available.append({"id": sid, "installed": (directory / "SKILL.md").is_file(),
                          "entrypoint": ".agents/skills/" + sid + "/SKILL.md"})
    return {"role": role_name, "stage": role["stage"], "mode": role["mode"],
            "purpose": role["purpose"], "handoff": role["handoff"],
            "skills": available, "context": context_files,
            "trust": "Proposed scope, not runtime permissions or agent attestation."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("list")
    pplan = sub.add_parser("plan")
    pplan.add_argument("role")
    pplan.add_argument("--working", action="append", default=[])
    args = p.parse_args()
    try:
        if args.cmd == "check":
            print("Validated " + str(len(load()["roles"])) + " specialist roles")
        elif args.cmd == "list":
            for name, role in load()["roles"].items():
                print(name + ": " + role["stage"] + "/" + role["mode"])
        else:
            print(json.dumps(plan(args.role, args.working), indent=2))
    except (AgentError, context.ContextError, skills.SkillError, ValueError, OSError, TypeError, KeyError) as e:
        print("agents: " + str(e), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
