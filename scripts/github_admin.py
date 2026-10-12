#!/usr/bin/env python3
"""Explicit, idempotent GitHub repository-administration setup.

The default is read-only preview. --apply requires OWNER confirmation, a
distinct qualified reviewer, and owner-scoped GitHub administration credentials.
Never print tokens, introduce bypass actors, or weaken unrelated rulesets.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

TOPICS = ("ai-agents","agentic-coding","software-engineering","github-template",
          "agent-skills","developer-tools","open-source")
CHECKS = ("template-contracts","pr-risk","sdk-compatibility (3.11)",
          "sdk-compatibility (3.13)","actions-security","browser-fixtures","harness-cli")
RULESET_NAME = "Open ASS: protected main and independent review"
GH_ACTIONS_APP_ID = 15368

class AdminError(ValueError): pass

def validate_repo(repo):
    if not isinstance(repo,str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",repo):
        raise AdminError("invalid GitHub repository")
    return repo

def ruleset(branch="main",require_codeowners=False):
    if not isinstance(branch,str) or not re.fullmatch(r"[A-Za-z0-9._/-]{1,200}",branch) or ".." in branch:
        raise AdminError("invalid protected branch")
    return {"name":RULESET_NAME,"target":"branch","enforcement":"active",
            "bypass_actors":[],
            "conditions":{"ref_name":{"include":["refs/heads/"+branch],"exclude":[]}},
            "rules":[{"type":"deletion"},{"type":"non_fast_forward"},
                {"type":"required_status_checks","parameters":{
                    "strict_required_status_checks_policy":True,
                    "do_not_enforce_on_create":False,
                    "required_status_checks":[{"context":name,"integration_id":GH_ACTIONS_APP_ID}
                                              for name in CHECKS]}},
                {"type":"pull_request","parameters":{
                    "dismiss_stale_reviews_on_push":True,
                    "require_code_owner_review":bool(require_codeowners),
                    "require_last_push_approval":True,
                    "required_approving_review_count":1,
                    "required_review_thread_resolution":True,
                    "allowed_merge_methods":["squash","merge","rebase"]}}]}

def plan(repo,metadata,existing,require_codeowners=False):
    validate_repo(repo)
    if not isinstance(metadata,dict) or metadata.get("full_name","").lower()!=repo.lower():
        raise AdminError("GitHub repository metadata does not match the requested repository")
    if not isinstance(existing,list):raise AdminError("cannot inspect current rulesets")
    selected=[x for x in existing if x.get("name")==RULESET_NAME]
    if len(selected)>1:raise AdminError("multiple Open ASS rulesets; resolve manually")
    branch=metadata.get("default_branch")
    if not isinstance(branch,str):raise AdminError("missing default branch")
    desired=ruleset(branch,require_codeowners)
    topics=sorted(set(metadata.get("topics") or [])|set(TOPICS))
    return {"repository":repo,"changes":{
        "enable_template":metadata.get("is_template") is not True,
        "topics":topics,
        "ruleset_action":"update" if selected else "create",
        "ruleset_id":selected[0]["id"] if selected else None,
        "ruleset":desired},
        "warnings":[
            "An approving independent collaborator is required. Sole maintainers can lock themselves out.",
            "CODEOWNERS checks are optional until at least two authorized owners are configured.",
            "Required browser checks run on every PR; GitHub repository settings are not changed during preview.",
            "GitHub rulesets are the enforceable authority; instructions and CLI guards are not."]}

def token_from_environment():
    found=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if found:return found
    try:
        result=subprocess.run(["gh","auth","token"],capture_output=True,text=True,timeout=8,check=False)
        if result.returncode==0 and result.stdout.strip():return result.stdout.strip()
    except (OSError,subprocess.TimeoutExpired):
        pass
    raise AdminError("an admin-capable GitHub token or authenticated gh CLI is required; don't paste tokens in chat")

def github_api(method,path,body=None,token=None):
    if not re.fullmatch(r"/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/topics|/rulesets(?:/[0-9]+)?|/collaborators\?per_page=100)?",path):
        raise AdminError("unapproved GitHub API endpoint")
    if method not in ("GET","PATCH","POST","PUT"):raise AdminError("unapproved GitHub API method")
    if method!="GET" and not token:raise AdminError("GitHub administration token required")
    headers={"Accept":"application/vnd.github+json",
             "X-GitHub-Api-Version":"2022-11-28","User-Agent":"open-ass-admin/1"}
    if token:headers["Authorization"]="Bearer "+token
    data=None if body is None else json.dumps(body).encode("utf-8")
    if data is not None:headers["Content-Type"]="application/json"
    request=urllib.request.Request("https://api.github.com"+path,data=data,
                                   headers=headers,method=method)
    try:
        with urllib.request.urlopen(request,timeout=20) as response:
            if response.url.split("/")[2]!="api.github.com":
                raise AdminError("untrusted GitHub API redirect")
            data=response.read(2_000_001)
            if len(data)>2_000_000:raise AdminError("GitHub response exceeds size limit")
            return json.loads(data)
    except urllib.error.HTTPError as exc:
        raise AdminError("GitHub API request failed: HTTP "+str(exc.code)+" on "+path) from None

def apply(repo,preview,token,request=github_api):
    validate_repo(repo)
    if not token:raise AdminError("admin token required")
    root="/repos/"+repo
    changes=preview["changes"]
    outcomes=[]
    reviewers=request("GET",root+"/collaborators?per_page=100",token=token)
    if not isinstance(reviewers,list) or len(reviewers)>=100:
        raise AdminError("cannot exhaustively confirm independent reviewers")
    original_owner=repo.split("/",1)[0].lower()
    eligible=[person for person in reviewers if isinstance(person,dict)
              and str(person.get("login","")).lower()!=original_owner
              and (person.get("permissions") or {}).get("push") is True]
    if not eligible:
        raise AdminError("no distinct write-access reviewer: invite a collaborator first")
    if changes["enable_template"]:
        request("PATCH",root,{"is_template":True},token=token)
        outcomes.append("template enabled")
    request("PUT",root+"/topics",{"names":changes["topics"]},token=token)
    outcomes.append("topics configured")
    action=changes["ruleset_action"]
    if action=="update":
        rid=changes["ruleset_id"]
        if type(rid)!=int or rid<=0:raise AdminError("invalid ruleset id")
        request("PUT",root+"/rulesets/"+str(rid),changes["ruleset"],token=token)
    elif action=="create":
        request("POST",root+"/rulesets",changes["ruleset"],token=token)
    else:raise AdminError("invalid ruleset plan")
    outcomes.append("protected ruleset "+action+"d")
    return outcomes

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",default="BradKhan/open-ASS")
    p.add_argument("--apply",action="store_true")
    p.add_argument("--confirm",help="Must exactly match OWNER/REPO for --apply")
    p.add_argument("--reviewer-ready",action="store_true",
                   help="I have a second authorized human collaborator who can approve PRs")
    p.add_argument("--require-codeowners",action="store_true",
                   help="Only after a second independent code owner is in CODEOWNERS")
    a=p.parse_args()
    try:
        validate_repo(a.repo)
        root="/repos/"+a.repo
        metadata=github_api("GET",root)
        existing=github_api("GET",root+"/rulesets")
        preview=plan(a.repo,metadata,existing,a.require_codeowners)
        print(json.dumps(preview,indent=2))
        if not a.apply:
            print("DRY RUN. No GitHub settings changed.")
            return
        if a.confirm!=a.repo or not a.reviewer_ready:
            raise AdminError("--apply requires --confirm OWNER/REPO and --reviewer-ready")
        print(json.dumps({"applied":apply(a.repo,preview,token_from_environment())},indent=2))
    except (AdminError,OSError,ValueError,KeyError,TypeError) as exc:
        print("github-admin: "+str(exc),file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":main()
