#!/usr/bin/env python3
"""Run one scoped coding-agent task with durable leases, cancellation and recovery.

No inferred approval, self-merge, or claim that estimated dollars are a provider cap.
The execution host must still enforce filesystem/network sandbox boundaries.
"""
import argparse
import hashlib
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

try:
    from scripts import agents, harness, lifecycle
except ModuleNotFoundError:
    import agents, harness, lifecycle

ROOT = Path(__file__).resolve().parents[1]
class SupervisorError(ValueError): pass

def init(db):
    db.execute("""CREATE TABLE IF NOT EXISTS attempts(
      task TEXT NOT NULL, revision INTEGER NOT NULL, harness TEXT NOT NULL,
      actor TEXT NOT NULL, worker_pid INTEGER NOT NULL, agent_pid INTEGER NOT NULL DEFAULT 0,
      heartbeat REAL NOT NULL, status TEXT NOT NULL, result_json TEXT,
      PRIMARY KEY(task,revision))""")

def alive(pid):
    if type(pid)!=int or pid <= 0: return False
    try:
        os.kill(pid,0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True

def previous(db, task):
    row=db.execute("SELECT * FROM attempts WHERE task=? ORDER BY revision DESC LIMIT 1",(task,)).fetchone()
    return dict(row) if row else None

def heartbeat(db,task,rev,agent_pid=None):
    if agent_pid is None:
        db.execute("UPDATE attempts SET heartbeat=? WHERE task=? AND revision=? AND status='running'",
                   (time.time(),task,rev))
    else:
        db.execute("UPDATE attempts SET heartbeat=?, agent_pid=? WHERE task=? AND revision=? AND status='running'",
                   (time.time(),agent_pid,task,rev))

def finish(db,task,rev,status,report):
    db.execute("UPDATE attempts SET status=?,result_json=?,heartbeat=? WHERE task=? AND revision=?",
               (status,json.dumps(report,sort_keys=True),time.time(),task,rev))

def safe_branch(root):
    result=subprocess.run(["git","branch","--show-current"],cwd=root,text=True,
                          capture_output=True,timeout=10,check=False)
    if result.returncode or not result.stdout.strip():
        raise SupervisorError("execution requires a named local Git branch")
    name=result.stdout.strip()
    if name in ("main","master"):
        raise SupervisorError("refusing writable agent execution on the default branch")
    return name

def terminate(process):
    if process.poll() is not None:return
    try:
        if os.name!="nt":os.killpg(process.pid,signal.SIGTERM)
        else:process.terminate()
        process.wait(timeout=5)
    except (ProcessLookupError,subprocess.TimeoutExpired):
        if process.poll() is None:
            if os.name!="nt":os.killpg(process.pid,signal.SIGKILL)
            else:process.kill()
            process.wait(timeout=5)

def run(db,task_id,runtime,role,actor,root=ROOT,timeout=900,reserve_cents=0,
        execute=False,ack_unmetered=False,include_skills=(),
        popen=subprocess.Popen,sleep=time.sleep,clock=time.monotonic):
    init(db)
    snapshot=lifecycle.show(db,task_id)
    if snapshot["state"]!="ready":raise SupervisorError("task must be ready")
    if role not in ("engineer","designer","writer"):
        raise SupervisorError("executor must be an implementation role")
    role_plan=agents.plan(role,root=root)
    if role_plan["mode"]!="write-branch":raise SupervisorError("role must be branch-write")
    cmd=harness.command(runtime,"write-branch")
    if type(timeout)!=int or not 1<=timeout<=3600:raise SupervisorError("invalid timeout")
    if type(reserve_cents)!=int or reserve_cents<=0:
        raise SupervisorError("reserve-cents must be positive")
    if reserve_cents>snapshot["budget"]-snapshot["spent"]:
        raise SupervisorError("insufficient reserved task budget")
    if not execute:
        return {"status":"dry-run","task":task_id,"harness":runtime,"role":role,
                "argv":cmd,"reserve_cents":reserve_cents,
                "note":"No inference or task-state mutation. Use --execute and --ack-unmetered."}
    if not ack_unmetered:
        raise SupervisorError("runtime has no proven hard dollar cap; pass --ack-unmetered to authorize")
    safe_branch(root)
    if not shutil_which(cmd[0]):raise SupervisorError("agent CLI missing: "+cmd[0])
    prompt=harness.make_prompt(role,root=root,include_skills=include_skills)
    # Criteria are mandatory context, not an instruction to change approval policy.
    prompt += "\n\nACCEPTED ISSUE #"+str(snapshot["issue"])+":\n"+snapshot["criteria"]
    started=lifecycle.transition(db,task_id,"start",actor,snapshot["rev"],spend=reserve_cents)
    rev=started["rev"]
    db.execute("INSERT INTO attempts(task,revision,harness,actor,worker_pid,heartbeat,status) VALUES (?,?,?,?,?,?,?)",
               (task_id,rev,runtime,actor,os.getpid(),time.time(),"running"))
    directory=root/".openass"/"runs"
    directory.mkdir(parents=True,exist_ok=True)
    if directory.is_symlink() or not directory.resolve().is_relative_to(root.resolve()):
        raise SupervisorError("unsafe runtime artifact directory")
    prefix=f"{task_id}-{rev}"
    result={"task":task_id,"attempt_revision":rev,"harness":runtime,"role":role,
            "budget_reservation_cents":reserve_cents,
            "actual_provider_cost_cents":None,
            "note":"Reservation is NOT measured spend; host must set actual provider billing limits."}
    process=None
    status="failed"
    try:
        with (directory/(prefix+".stdout")).open("wb") as stdout, (directory/(prefix+".stderr")).open("wb") as stderr:
            os.chmod(stdout.name,0o600)
            os.chmod(stderr.name,0o600)
            process=popen(cmd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,cwd=root,
                          start_new_session=(os.name!="nt"))
            heartbeat(db,task_id,rev,process.pid)
            process.stdin.write(prompt.encode("utf-8"))
            process.stdin.close()
            deadline=clock()+timeout
            while process.poll() is None:
                if lifecycle.show(db,task_id)["state"]=="cancelled":
                    status="cancelled"
                    terminate(process)
                    break
                if clock()>deadline:
                    status="timeout"
                    terminate(process)
                    break
                heartbeat(db,task_id,rev)
                sleep(0.25)
            code=process.wait()
        result.update(exit_code=code,
                      stdout_sha256=hashlib.sha256((directory/(prefix+".stdout")).read_bytes()).hexdigest(),
                      stderr_sha256=hashlib.sha256((directory/(prefix+".stderr")).read_bytes()).hexdigest())
        if status=="failed" and code==0:status="verifying"
        result["status"]=status
    except BaseException as exc:
        if process is not None and process.poll() is None:
            terminate(process)
        result.update(status="failed",failure=type(exc).__name__)
        raise
    finally:
        actual=lifecycle.show(db,task_id)
        if actual["state"]=="running":
            lifecycle.transition(db,task_id,"verify" if status=="verifying" else "fail",
                                 actor,actual["rev"])
        finish(db,task_id,rev,status,result)
    return result

def shutil_which(binary):
    import shutil
    return shutil.which(binary)

def recover(db,task_id,actor,stale_seconds=120,now=None,process_alive=alive):
    init(db)
    if type(stale_seconds)!=int or stale_seconds<30:
        raise SupervisorError("stale threshold must be >=30 seconds")
    row=lifecycle.show(db,task_id)
    if row["state"]!="running":raise SupervisorError("recovery only applies to running tasks")
    attempt=previous(db,task_id)
    if attempt is None:raise SupervisorError("run lease missing; manual reconciliation required")
    now=time.time() if now is None else now
    if now-attempt["heartbeat"]<stale_seconds:raise SupervisorError("worker heartbeat is not stale")
    if process_alive(attempt["worker_pid"]) or process_alive(attempt["agent_pid"]):
        raise SupervisorError("worker or agent process still alive; refusing duplicate execution")
    result=lifecycle.transition(db,task_id,"fail",actor,row["rev"])
    finish(db,task_id,attempt["revision"],"interrupted",{"status":"interrupted","recovered":True})
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db",type=Path,default=lifecycle.DEFAULT_DB)
    sub=p.add_subparsers(dest="action",required=True)
    a=sub.add_parser("run")
    a.add_argument("task")
    a.add_argument("--harness",choices=tuple(harness.HARNESSES),required=True)
    a.add_argument("--role",choices=("engineer","designer","writer"),default="engineer")
    a.add_argument("--actor",required=True)
    a.add_argument("--timeout",type=int,default=900)
    a.add_argument("--reserve-cents",type=int,required=True)
    a.add_argument("--include-skill",action="append",default=[])
    a.add_argument("--execute",action="store_true")
    a.add_argument("--ack-unmetered",action="store_true")
    r=sub.add_parser("recover")
    r.add_argument("task");r.add_argument("--actor",required=True)
    r.add_argument("--stale-seconds",type=int,default=120)
    args=p.parse_args()
    try:
        with lifecycle.connect(args.db) as db:
            if args.action=="run":
                result=run(db,args.task,args.harness,args.role,args.actor,
                           timeout=args.timeout,reserve_cents=args.reserve_cents,
                           execute=args.execute,ack_unmetered=args.ack_unmetered,
                           include_skills=args.include_skill)
            else:result=recover(db,args.task,args.actor,args.stale_seconds)
        print(json.dumps(result,indent=2))
    except (SupervisorError,lifecycle.LifecycleError,agents.AgentError,
            harness.HarnessError,sqlite3.Error,ValueError,OSError) as exc:
        print("supervisor: "+str(exc),file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":main()
