#!/usr/bin/env python3
"""Drive a scoped task through agent execution, verification and PR review handoff.

Never grants merge rights or treats an agent's success message as acceptance.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
try:
    from scripts import attest, lifecycle, supervisor, activation
except ModuleNotFoundError:
    import attest, lifecycle, supervisor, activation

ROOT=Path(__file__).resolve().parents[1]
class DispatchError(ValueError):pass

def local_head(root=ROOT,runner=subprocess.run):
    r=runner(["git","rev-parse","HEAD"],cwd=root,capture_output=True,
             text=True,timeout=12,check=False)
    head=(r.stdout or "").strip()
    if r.returncode or not re.fullmatch("[a-f0-9]{40}",head):
        raise DispatchError("cannot determine exact Git head")
    clean=runner(["git","status","--porcelain"],cwd=root,capture_output=True,
                 text=True,timeout=12,check=False)
    if clean.returncode or clean.stdout.strip():
        raise DispatchError("commit all work before a review handoff")
    return head

def verify_project(root=ROOT,runner=subprocess.run):
    config=json.loads((root/"config/project.json").read_text(encoding="utf-8"))
    if config.get("initialized") is not True:
        raise DispatchError("configure actual application checks before verification")
    r=runner([sys.executable,"scripts/verify.py"],cwd=root,capture_output=True,
             text=True,timeout=600,check=False)
    if r.returncode:
        raise DispatchError("application verifier returned exit "+str(r.returncode))
    output=((r.stdout or "")+"\n"+(r.stderr or "")).encode()
    return {"exit_code":0,"output_sha256":hashlib.sha256(output).hexdigest()}

def verify_revision(root,head,verifier=verify_project,runner=subprocess.run):
    """Run checks in a clean detached Git checkout of an immutable commit."""
    if not re.fullmatch(r"[0-9a-f]{40}",str(head)):
        raise DispatchError("invalid immutable revision")
    with tempfile.TemporaryDirectory(prefix="openass-verify-") as name:
        checkout=Path(name)/"source"
        command=["git","worktree","add","--detach",str(checkout),head]
        result=runner(command,cwd=root,capture_output=True,text=True,timeout=90,check=False)
        if result.returncode:
            raise DispatchError("cannot construct detached verification checkout")
        try:
            pinned=runner(["git","rev-parse","HEAD"],cwd=checkout,
                          capture_output=True,text=True,timeout=15,check=False)
            if pinned.returncode or (pinned.stdout or "").strip()!=head:
                raise DispatchError("checkout does not match PR revision")
            verified=verifier(root=checkout)
            if not isinstance(verified,dict) or verified.get("exit_code")!=0:
                raise DispatchError("verifier did not report success")
            status=runner(["git","status","--porcelain"],cwd=checkout,
                          capture_output=True,text=True,timeout=15,check=False)
            if status.returncode or (status.stdout or "").strip():
                raise DispatchError("verification changed tracked or untracked checkout files")
            return dict(verified,head_sha=head,checkout="detached-immutable-revision")
        finally:
            runner(["git","worktree","remove","--force",str(checkout)],cwd=root,
                   capture_output=True,text=True,timeout=30,check=False)


def matching_pr(repo,number,head,fetch=attest.api_get):
    if not re.fullmatch("[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",str(repo)):
        raise DispatchError("valid GitHub repository required")
    if type(number)!=int or number<=0:
        raise DispatchError("valid PR number required")
    pr=fetch("/repos/"+repo+"/pulls/"+str(number))
    if pr.get("state")!="open" or pr.get("head",{}).get("sha")!=head:
        raise DispatchError("open PR head differs from local reviewed head")
    base=(pr.get("base") or {}).get("repo") or {}
    if base.get("full_name","").lower()!=repo.lower():
        raise DispatchError("PR base repository mismatch")
    return {"number":number,"head_sha":head,"url":pr.get("html_url")}

def dispatch(db,task_id,runtime,actor,repo=None,pr=None,reserve_cents=0,timeout=900,
             execute=False,ack_unmetered=False,max_attempts=1,root=ROOT,
             execute_agent=supervisor.run,verifier=verify_project,fetch_pr=matching_pr,
             commit_verifier=verify_revision,working=(),strict_skills=False):
    if type(max_attempts)!=int or not 1<=max_attempts<=3:
        raise DispatchError("max_attempts must be 1..3")
    record=lifecycle.show(db,task_id)
    if record["state"] not in ("ready","failed","verifying"):
        raise DispatchError("task is not ready, failed, or verifying")
    plan=activation.select(record["criteria"],list(working),root=root,strict=strict_skills)
    if plan["requires_clarification"] and record["state"] in ("ready","failed"):
        raise DispatchError("unresolved requirements; clarify acceptance criteria before inference")
    if not execute:
        return {"task":task_id,"activation":plan,"status":"dry-run","state":record["state"],
                "harness":runtime,"max_attempts":max_attempts,
                "note":"No inference. Use --execute --ack-unmetered to run."}
    if not ack_unmetered:
        raise DispatchError("explicit --ack-unmetered required")
    result={"task":task_id,"harness":runtime,"activation":plan,"attempts":[]}
    for _ in range(max_attempts):
        if record["state"]=="failed":
            record=lifecycle.transition(db,task_id,"retry",actor,record["rev"])
        if record["state"]=="ready":
            run=execute_agent(db,task_id,runtime,plan["primary_role"],actor,root=root,timeout=timeout,
                              reserve_cents=reserve_cents,execute=True,ack_unmetered=True,
                              include_skills=plan["skill_ids"])
            result["attempts"].append({"status":run["status"],
                                       "exit_code":run.get("exit_code"),
                                       "provider_reported_cost_cents":run.get("provider_reported_cost_cents")})
            record=lifecycle.show(db,task_id)
        if record["state"] in ("verifying","cancelled"):
            break
        if record["state"]!="failed":
            raise DispatchError("runner returned inconsistent task state")
    if record["state"]=="failed":
        result["status"]="failed"
        return result
    if record["state"]=="cancelled":
        result["status"]="cancelled"
        return result
    if pr is None:
        result["verification"]=verifier(root=root)
        result["verification"]["scope"]="preliminary-working-tree"
        result["status"]="awaiting-pull-request"
        return result
    head=local_head(root)
    review_pr=fetch_pr(repo,pr,head)
    result["verification"]=commit_verifier(root,head,verifier)
    if result["verification"].get("head_sha")!=head:
        raise DispatchError("verification evidence does not match PR commit")
    # Reject PR advances or branch movements during test execution.
    if local_head(root)!=head or fetch_pr(repo,pr,head).get("head_sha")!=head:
        raise DispatchError("PR or checkout changed during verification")
    next_state=lifecycle.transition(db,task_id,"review",actor,record["rev"],head_sha=head)
    result.update(status="awaiting-independent-review",pr=review_pr,
                  state=next_state["state"],head_sha=head,
                  note="An authorized independent human reviewer must approve the current PR head.")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db",type=Path,default=lifecycle.DEFAULT_DB)
    p.add_argument("task");p.add_argument("--harness",choices=("codex","claude","hermes"),required=True)
    p.add_argument("--actor",required=True)
    p.add_argument("--reserve-cents",type=int,default=100)
    p.add_argument("--timeout",type=int,default=900)
    p.add_argument("--max-attempts",type=int,default=1)
    p.add_argument("--repo");p.add_argument("--pr",type=int)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--ack-unmetered",action="store_true")
    p.add_argument("--working",action="append",default=[])
    p.add_argument("--strict-skills",action="store_true")
    a=p.parse_args()
    try:
        with lifecycle.connect(a.db) as db:
            report=dispatch(db,a.task,a.harness,a.actor,a.repo,a.pr,a.reserve_cents,
                            a.timeout,a.execute,a.ack_unmetered,a.max_attempts,
                            working=a.working,strict_skills=a.strict_skills)
        print(json.dumps(report,indent=2))
        if report["status"] in ("failed","cancelled"):
            raise SystemExit(1)
    except (DispatchError,lifecycle.LifecycleError,supervisor.SupervisorError,
            attest.AttestError,ValueError,OSError,subprocess.TimeoutExpired) as exc:
        print("dispatch: "+str(exc),file=sys.stderr)
        raise SystemExit(1)
if __name__=="__main__":main()
