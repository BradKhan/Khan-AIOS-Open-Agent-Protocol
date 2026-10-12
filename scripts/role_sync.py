#!/usr/bin/env python3
"""Generate Claude specialist definitions from the one role registry."""
import argparse
import sys
from pathlib import Path
try:
    from scripts import agents
except ModuleNotFoundError:
    import agents
ROOT=Path(__file__).resolve().parents[1]
def render(name,role):
    tools="Read, Grep, Glob, Edit, Write, Bash" if role["mode"]=="write-branch" else "Read, Grep, Glob"
    return (f"---\nname: {name}\ndescription: {role['purpose']}\ntools: {tools}\n---\n\n"
            f"# {name}\n\n{role['purpose']}\n\nStage: {role['stage']}; mode: {role['mode']}.\n\n"
            f"Prepare scope with python3 scripts/agents.py plan {name}.\n"
            "Follow AGENTS.md and POLICY.md; host permissions govern actual tools.\n"
            f"Expected handoff: {role['handoff']}\n")
def synchronize(root=ROOT,write=False):
    target=root/".claude/agents"
    if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("agent path escapes repository")
    roles=agents.load(root)["roles"]
    missing=[]
    for name,role in sorted(roles.items()):
        p=target/(name+".md")
        if p.is_symlink():raise ValueError("symlinked role")
        content=render(name,role)
        if not p.is_file() or p.read_text()!=content:missing.append((p,content))
    if write:
        target.mkdir(parents=True,exist_ok=True)
        for p,content in missing:p.write_text(content)
    elif missing:raise ValueError("roles drifted: "+", ".join(p.name for p,_ in missing))
    return len(roles)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("check","write"))
    try:print("Role definitions: "+str(synchronize(write=p.parse_args().action=="write")))
    except (ValueError,OSError,agents.AgentError) as e:
        print("role-sync: "+str(e),file=sys.stderr);raise SystemExit(1)
if __name__=="__main__":main()
