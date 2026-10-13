#!/usr/bin/env python3
"""Risk-adaptive task classifier and role-bound skill activation.

Deterministic rules, never an LLM inference or authorization boundary.
Only skills declared for a role and actually installed may enter its prompt.
"""
import argparse
import json
import re
import sys
from pathlib import Path
try:
    from scripts import agents, pr_gate, skills
except ModuleNotFoundError:
    import agents, pr_gate, skills

ROOT=Path(__file__).resolve().parents[1]
TIERS=("fast","standard","critical")
WEB_EXT={".tsx",".jsx",".css",".scss",".vue",".svelte"}
WRITE_WORDS=("copywriting","rewrite copy","marketing copy","landing page copy","humanize","tone of voice")
DESIGN_WORDS=("visual design","ui design","design system","responsive design","layout","accessibility","redesign")
UNCERTAIN_WORDS=("tbd","to be decided","not sure which","figure out requirements")
class ActivationError(ValueError):pass

def select(description,paths=(),risk="standard",root=ROOT,strict=False):
    if not isinstance(description,str) or not description.strip() or len(description)>20000:
        raise ActivationError("task description must be bounded nonempty text")
    if risk not in TIERS:raise ActivationError("invalid requested risk tier")
    if not isinstance(paths,(list,tuple)) or len(paths)>100 or any(not isinstance(p,str) or not p or len(p)>500 for p in paths):
        raise ActivationError("invalid working paths")
    inferred=pr_gate.required_risk(list(paths)) if paths else "fast"
    effective=TIERS[max(TIERS.index(risk),TIERS.index(inferred))]
    text=description.lower()
    suffixes={Path(p).suffix.lower() for p in paths}
    web=bool(suffixes&WEB_EXT) or any(x in text for x in ("website","frontend","user interface","dashboard","accessibility"))
    writing=any(x in text for x in WRITE_WORDS)
    design=bool(web and (suffixes&{".css",".scss"} or any(x in text for x in DESIGN_WORDS)))
    if writing and not design:primary="writer"
    elif design:primary="designer"
    else:primary="engineer"
    requested={
        "engineer":["test-driven-development","verification-before-completion"],
        "designer":["design-taste-frontend","web-design-guidelines","impeccable"],
        "writer":["humanizer"]
    }[primary]
    roles=agents.load(root)["roles"]
    if primary not in roles or roles[primary]["mode"]!="write-branch":
        raise ActivationError("required implementation role not defined")
    allowed=set(roles[primary]["skills"])
    if not set(requested)<=allowed:
        raise ActivationError("activation requested skills outside role registry")
    # File existence is not proof of a vetted installation. Before adding
    # third-party instructions to an agent prompt, verify installer provenance
    # and every installed file hash against the pinned catalog receipt.
    candidates=[]
    for skill in requested:
        target=root/".agents/skills"/skill/"SKILL.md"
        if target.is_file() and not target.is_symlink() and not target.parent.is_symlink():
            candidates.append(skill)
    audited=set(skills.audit(root)) if candidates else set()
    installed=[skill for skill in requested if skill in audited]
    missing=[skill for skill in requested if skill not in audited]
    if strict and missing:
        raise ActivationError("required skills not installed: "+", ".join(missing))
    review_roles=["reviewer"]
    if web:review_roles.append("qa")
    if effective=="critical":review_roles.append("security-reviewer")
    ambiguities=[x for x in UNCERTAIN_WORDS if x in text]
    return {"primary_role":primary,"skill_ids":installed,"missing_skill_ids":missing,
            "review_roles":review_roles,"risk":effective,
            "requires_clarification":bool(ambiguities),
            "clarification_triggers":ambiguities,
            "mode":"write-branch",
            "policy":"Uninstalled skills are never claimed as activated; reviewers remain distinct."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--description",required=True)
    p.add_argument("--path",action="append",default=[])
    p.add_argument("--risk",choices=TIERS,default="standard")
    p.add_argument("--strict",action="store_true")
    args=p.parse_args()
    try:print(json.dumps(select(args.description,args.path,args.risk,strict=args.strict),indent=2))
    except (ActivationError,agents.AgentError,skills.SkillError,ValueError,OSError) as exc:
        print("activate: "+str(exc),file=sys.stderr);raise SystemExit(1)
if __name__=="__main__":main()
