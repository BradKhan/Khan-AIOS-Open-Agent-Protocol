#!/usr/bin/env python3
"""Safe dry-run-first initialization with explicit downstream ownership."""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class SetupError(ValueError): pass

def build(root, name, owner, tier, app_check, security_check=None):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ -]{0,79}", name):
        raise SetupError("invalid project name")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", owner) or "--" in owner:
        raise SetupError("invalid GitHub owner")
    if tier not in ("fast", "standard", "critical"):
        raise SetupError("invalid tier")
    for command in (app_check, security_check):
        if command is not None and (not isinstance(command, list) or not command or
                                    any(not isinstance(x,str) or not x for x in command)):
            raise SetupError("expected argv array")
    if not app_check or (tier=="critical" and not security_check):
        raise SetupError("application checks and critical security command required")
    cfg=root/"config/project.json"; owners=root/".github/CODEOWNERS"
    if any(not p.is_file() or p.is_symlink() for p in (cfg,owners)):
        raise SetupError("missing or symlinked config")
    obj=json.loads(cfg.read_text())
    if obj.get("initialized"): raise SetupError("project already initialized")
    obj.update(initialized=True,project_name=name,assurance_tier=tier)
    obj["verification"]={"application_command":app_check,"security_command":security_check}
    txt="# Destination project's owner. Configure GitHub rulesets to enforce.\n"
    txt+="".join(f"{p} @{owner}\n" for p in ("*",".github/","scripts/","config/","integrations/"))
    return {cfg:json.dumps(obj,indent=2)+"\n", owners:txt}

def apply(changes):
    for path in changes:
        if path.is_symlink(): raise SetupError("refusing symlink")
    for path, content in changes.items():
        tmp=None
        try:
            with tempfile.NamedTemporaryFile("w",dir=path.parent,encoding="utf8",delete=False) as f:
                tmp=Path(f.name);f.write(content)
            os.replace(tmp,path)
        finally:
            if tmp and tmp.exists():tmp.unlink()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--name",required=True);p.add_argument("--owner",required=True)
    p.add_argument("--tier",choices=("fast","standard","critical"),default="standard")
    p.add_argument("--security-check",nargs="+");p.add_argument("--apply",action="store_true")
    p.add_argument("--app-check",nargs="+",required=True)
    a=p.parse_args()
    try:
        changes=build(ROOT,a.name,a.owner,a.tier,a.app_check,a.security_check)
        if a.apply:
            apply(changes);print("Initialized; review architecture and run verification.")
        else:print("DRY RUN: "+", ".join(str(p.relative_to(ROOT)) for p in changes))
    except (ValueError,OSError) as ex:
        print("bootstrap: "+str(ex),file=sys.stderr);raise SystemExit(1)
if __name__=="__main__":main()
