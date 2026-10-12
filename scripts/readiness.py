#!/usr/bin/env python3
"""Read-only repository setup assessment; cannot alter GitHub configuration."""
import argparse
import json
import re
import sys
import urllib.request
class ReadinessError(ValueError):pass
def evaluate(repo,branch):
    if not isinstance(repo,dict) or not isinstance(branch,dict):raise ReadinessError("missing repository metadata")
    gaps=[]
    if repo.get("is_template") is not True:gaps.append("enable Template repository")
    if not repo.get("topics"):gaps.append("add GitHub repository topics")
    if branch.get("protected") is not True:gaps.append("enable default branch protection/ruleset")
    return {"ready":not gaps,"owner_actions":gaps,"warning":"Protected=true alone does not attest required check or reviewer policy."}
def fetch(url):
    if not url.startswith("https://api.github.com/repos/"):raise ReadinessError("unapproved API URL")
    req=urllib.request.Request(url,headers={"User-Agent":"open-ass-readiness/1"})
    with urllib.request.urlopen(req,timeout=15) as r:
        data=r.read(1_000_001)
        if len(data)>1_000_000:raise ReadinessError("oversized API result")
        return json.loads(data)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",required=True);p.add_argument("--strict",action="store_true")
    a=p.parse_args()
    if not re.fullmatch("[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",a.repo):p.error("invalid repo")
    try:
        repo=fetch("https://api.github.com/repos/"+a.repo)
        branch=fetch("https://api.github.com/repos/"+a.repo+"/branches/"+repo["default_branch"])
        report=evaluate(repo,branch)
        print(json.dumps(report,indent=2))
        if a.strict and not report["ready"]:raise SystemExit(1)
    except (ValueError,KeyError,OSError) as exc:
        print("readiness: "+str(exc),file=sys.stderr);raise SystemExit(1)
if __name__=="__main__":main()
