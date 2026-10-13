#!/usr/bin/env python3
"""Reproducible, opt-in coding-agent evaluation with independent acceptance.

The agent sees only task requirements and a failing starter file. Acceptance
cases remain in the controller. No fabricated costs or performance claims.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
try:
    from scripts import harness, live_smoke, sandbox, activation
except ModuleNotFoundError:
    import harness, live_smoke, sandbox, activation

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"evaluations/tasks.json"
STARTER="def solve(value):\n    raise NotImplementedError('implement solve(value)')\n"
CHECKER=(
    "import importlib.util,json,sys;"
    "s=importlib.util.spec_from_file_location('solution','/workspace/solution.py' if sys.argv[1]=='container' else 'solution.py');"
    "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
    "data=json.load(sys.stdin);"
    "print(json.dumps([m.solve(item) for item in data]))"
)
class EvaluationError(ValueError):pass

def load(path=MANIFEST):
    doc=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc,dict) or doc.get("version")!=1 or not isinstance(doc.get("tasks"),list):
        raise EvaluationError("invalid task manifest")
    tasks=doc["tasks"]
    if len(tasks)!=18:raise EvaluationError("expected 18 independent tasks")
    seen=set()
    for t in tasks:
        if not isinstance(t,dict) or set(t)!={"id","category","prompt","cases"}:
            raise EvaluationError("invalid task record")
        if not isinstance(t["id"],str) or not re.fullmatch(r"[a-z][a-z0-9-]{2,63}",t["id"]) or t["id"] in seen:
            raise EvaluationError("duplicate or invalid task id")
        seen.add(t["id"])
        if not isinstance(t["prompt"],str) or not 15<=len(t["prompt"])<=1500:
            raise EvaluationError("invalid task prompt")
        if not isinstance(t["category"],str) or t["category"] not in ("text","data","logic","math","security"):
            raise EvaluationError("invalid task category")
        if not isinstance(t["cases"],list) or not 3<=len(t["cases"])<=10:
            raise EvaluationError("task needs held-back acceptance cases")
        for case in t["cases"]:
            if not isinstance(case,dict) or set(case)!={"input","expected"}:
                raise EvaluationError("invalid acceptance case")
            json.dumps(case)
    return tasks

def plan(tasks=None):
    tasks=load() if tasks is None else tasks
    return {"suite":"openass-coding-v1","tasks":len(tasks),
            "cases":sum(len(t["cases"]) for t in tasks),
            "starter_sha256":hashlib.sha256(STARTER.encode()).hexdigest(),
            "costs":"unknown until trustworthy provider telemetry",
            "scope":"isolated coding tasks; not proven productivity gain"}

def prepare(workspace,task,mode="baseline"):
    if mode not in ("baseline","openass"):raise EvaluationError("unknown experimental mode")
    workspace.mkdir(parents=True,exist_ok=True)
    (workspace/"solution.py").write_text(STARTER,encoding="utf-8")
    instructions=("Edit only solution.py. Implement solve(value) for JSON-serializable "
                  "inputs and outputs. Return a Python implementation, not an explanation. "
                  "Do not change any other file, commit, push or access private resources.\n\n"+task["prompt"])
    if mode=="openass":
        instructions+=("\n\nOpen ASS engineering contract: inspect requirements, handle edge "
                       "cases, test assumptions, avoid gratuitous dependencies and confirm "
                       "actual behavior rather than declaring success.")
        (workspace/"AGENTS.md").write_text(
            "# Open ASS fixture\nScope: solution.py only. No secrets, network, commits, PRs or deployment.\n")
    (workspace/"TASK.md").write_text(instructions)
    return instructions

def verify(workspace,cases,backend="container",image=None,runner=subprocess.run):
    if backend not in ("container","unsafe-local"):
        raise EvaluationError("verification backend must be an isolated container or explicitly unsafe-local")
    inputs=[case["input"] for case in cases]
    if backend=="container":
        argv=sandbox.wrap(["python3","-I","-c",CHECKER,"container"],workspace,image)
    else:
        argv=[sys.executable,"-I","-c",CHECKER,"local"]
    try:
        result=runner(argv,input=json.dumps(inputs),cwd=workspace,
                      capture_output=True,text=True,timeout=25,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {"passed":False,"error":type(exc).__name__}
    if result.returncode!=0:
        return {"passed":False,"error":"execution failed", "exit_code":result.returncode}
    try:
        observed=json.loads(result.stdout)
    except (ValueError,TypeError):
        return {"passed":False,"error":"non-JSON result"}
    expected=[c["expected"] for c in cases]
    return {"passed":observed==expected,"accepted_cases":sum(a==b for a,b in zip(observed,expected)),
            "total_cases":len(expected)}

def run_one(task,mode,runtime,image,budget_cents=100,backend="container",
            invoke=harness.execute):
    with tempfile.TemporaryDirectory(prefix="openass-eval-") as tmp:
        work=Path(tmp)
        prompt=prepare(work,task,mode)
        argv=live_smoke.plan(runtime,budget_cents)
        # No Git state required for a read-only acceptance evaluator, but the
        # coding CLI may require git. Initialize deterministic isolated fixture.
        live_smoke.prepare(work)
        start=time.monotonic()
        call=invoke(argv,prompt,root=work,timeout=180)
        elapsed=round(time.monotonic()-start,3)
        changed=[p.relative_to(work).as_posix() for p in work.iterdir()
                 if p.name not in (".git","solution.py","TASK.md","AGENTS.md",
                                   "acceptance.txt")]
        output=verify(work,task["cases"],backend,image) if call["exit_code"]==0 else {"passed":False,"error":"agent exit nonzero"}
        accepted=output.get("passed") is True and not changed
        return {"id":task["id"],"accepted":accepted,"elapsed_seconds":elapsed,
                "agent_exit_code":call["exit_code"],"verification":output,
                "unexpected_files":changed,"reported_cost_usd":None,
                "start_sha256":hashlib.sha256(STARTER.encode()).hexdigest()}

def compare(base,enhanced):
    if base.get("mode")!="baseline" or enhanced.get("mode")!="openass":
        raise EvaluationError("comparison requires baseline and openass")
    for field in ("suite","harness","model_version","task_ids","starter_sha256"):
        if base.get(field)!=enhanced.get(field):
            raise EvaluationError("comparison mismatch: "+field)
    def stats(report):
        rows=report.get("results")
        if not isinstance(rows,list) or len(rows)!=len(report["task_ids"]):
            raise EvaluationError("missing measured outcomes")
        costs=[x.get("reported_cost_usd") for x in rows]
        return {"accepted":sum(x.get("accepted") is True for x in rows),
                "tasks":len(rows),
                "elapsed_seconds":round(sum(x.get("elapsed_seconds",0) for x in rows),3),
                "cost_usd":round(sum(costs),4) if all(type(c) in (float,int) for c in costs) else None}
    return {"baseline":stats(base),"openass":stats(enhanced),
            "note":"Cost omitted when not measured; real model comparisons only, no imputed effects."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("plan")
    smoke=sub.add_parser("self-test")
    run=sub.add_parser("run")
    run.add_argument("--mode",choices=("baseline","openass"),required=True)
    run.add_argument("--harness",choices=tuple(harness.HARNESSES),required=True)
    run.add_argument("--model-version",required=True)
    run.add_argument("--image",required=True,help="Pre-pulled SHA256-pinned image containing Python for untrusted verification")
    run.add_argument("--budget-cents",type=int,default=100)
    run.add_argument("--task",action="append",default=[])
    run.add_argument("--execute",action="store_true")
    run.add_argument("--ack-paid-local-agent",action="store_true")
    run.add_argument("--out",type=Path)
    comp=sub.add_parser("compare")
    comp.add_argument("--baseline",type=Path,required=True)
    comp.add_argument("--openass",type=Path,required=True)
    a=p.parse_args()
    try:
        tasks=load()
        if a.action=="plan":result=plan(tasks)
        elif a.action=="self-test":
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                task=tasks[0]
                prepare(root,task)
                (root/"solution.py").write_text("def solve(value):\n    return ' '.join(reversed(value.split()))\n")
                result=verify(root,task["cases"],backend="unsafe-local")
                if not result["passed"]:raise EvaluationError("self-test reference failed")
                (root/"solution.py").write_text(STARTER)
                if verify(root,task["cases"],backend="unsafe-local")["passed"]:
                    raise EvaluationError("self-test accepted broken starter")
            result={"self_test":"pass","tasks":len(tasks)}
        elif a.action=="compare":
            result=compare(json.loads(a.baseline.read_text()),json.loads(a.openass.read_text()))
        else:
            selected=[t for t in tasks if not a.task or t["id"] in a.task]
            if not selected or (a.task and len(selected)!=len(set(a.task))):
                raise EvaluationError("unknown or duplicate task IDs")
            if not a.execute:
                result={"status":"dry-run","mode":a.mode,"tasks":[t["id"] for t in selected],
                        "note":"No paid inference. Add --execute --ack-paid-local-agent."}
            else:
                if not a.ack_paid_local_agent:
                    raise EvaluationError("must explicitly acknowledge paid local agent and untrusted code")
                if not shutil.which(a.harness):
                    raise EvaluationError("local harness executable unavailable")
                # Verify the digest-pinned Docker runner exists before incurring inference.
                if not a.image or "@sha256:" not in a.image:
                    raise EvaluationError("digest-pinned Docker image required")
                results=[run_one(t,a.mode,a.harness,a.image,a.budget_cents) for t in selected]
                result={"suite":"openass-coding-v1","mode":a.mode,"harness":a.harness,
                        "model_version":a.model_version,"task_ids":[t["id"] for t in selected],
                        "starter_sha256":hashlib.sha256(STARTER.encode()).hexdigest(),
                        "results":results}
                if a.out:a.out.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
    except (EvaluationError,sandbox.SandboxError,live_smoke.LiveSmokeError,
            harness.HarnessError,OSError,ValueError,subprocess.TimeoutExpired) as exc:
        print("eval-suite: "+str(exc),file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":
    main()
