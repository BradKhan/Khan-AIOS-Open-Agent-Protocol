#!/usr/bin/env python3
"""Transactional, resumable local task lifecycle. Never grants merge privileges."""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DB=ROOT/".openass"/"tasks.sqlite3"
STEPS={
    "proposed":{"clarify":"clarifying","ready":"ready","cancel":"cancelled"},
    "clarifying":{"ready":"ready","cancel":"cancelled"},
    "ready":{"start":"running","cancel":"cancelled"},
    "running":{"verify":"verifying","fail":"failed","cancel":"cancelled"},
    "verifying":{"review":"review","fail":"failed","cancel":"cancelled"},
    "review":{"changes":"ready","fail":"failed","accept":"accepted"},
    "failed":{"retry":"ready","cancel":"cancelled"},
    "accepted":{},"cancelled":{}
}
class LifecycleError(ValueError): pass

def connect(path=DEFAULT_DB):
    if path.is_symlink():raise LifecycleError("state database may not be a symlink")
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=15,isolation_level=None)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA busy_timeout=15000")
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""CREATE TABLE IF NOT EXISTS tasks(
      id TEXT PRIMARY KEY, issue INTEGER NOT NULL, criteria TEXT NOT NULL,
      state TEXT NOT NULL, rev INTEGER NOT NULL, budget INTEGER NOT NULL,
      spent INTEGER NOT NULL, retry_limit INTEGER NOT NULL, retries INTEGER NOT NULL,
      executor TEXT, head_sha TEXT);
      CREATE TABLE IF NOT EXISTS events(
      sequence INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT NOT NULL,
      revision INTEGER NOT NULL, action TEXT NOT NULL, actor TEXT NOT NULL,
      details TEXT NOT NULL, timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(task,revision));""")
    return db

def create(db,id,issue,criteria,budget=0,retry_limit=2):
    if not isinstance(id,str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,63}",id):
        raise LifecycleError("invalid task identifier")
    if not isinstance(issue,int) or issue<1 or not isinstance(criteria,str) or len(criteria.strip())<8:
        raise LifecycleError("issue and acceptance criteria required")
    if type(budget)!=int or type(retry_limit)!=int or budget<0 or retry_limit<0 or retry_limit>20:
        raise LifecycleError("invalid budgets or retry limit")
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                   (id,issue,criteria,"proposed",0,budget,0,retry_limit,0,None,None))
        db.execute("INSERT INTO events(task,revision,action,actor,details) VALUES (?,?,?,?,?)",
                   (id,0,"create","owner",json.dumps({"issue":issue})))
        db.execute("COMMIT")
    except sqlite3.IntegrityError as exc:
        db.execute("ROLLBACK");raise LifecycleError("task already exists") from exc
    return show(db,id)

def show(db,id):
    row=db.execute("SELECT * FROM tasks WHERE id=?",(id,)).fetchone()
    if row is None:raise LifecycleError("unknown task")
    result=dict(row)
    result["events"]=[dict(e) for e in db.execute(
        "SELECT revision,action,actor,details,timestamp FROM events WHERE task=? ORDER BY revision",(id,))]
    return result

def transition(db,id,action,actor,expected,spend=0,head_sha=None,verified=False):
    if not isinstance(actor,str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,80}",actor):
        raise LifecycleError("actor required")
    if type(expected)!=int or expected<0 or type(spend)!=int or spend<0:
        raise LifecycleError("invalid revision or cost")
    db.execute("BEGIN IMMEDIATE")
    try:
        row=db.execute("SELECT * FROM tasks WHERE id=?",(id,)).fetchone()
        if row is None:raise LifecycleError("unknown task")
        row=dict(row)
        if row["rev"]!=expected:raise LifecycleError("stale revision")
        state=STEPS.get(row["state"],{}).get(action)
        if state is None:raise LifecycleError("invalid state transition")
        if row["spent"]+spend>row["budget"]:
            raise LifecycleError("budget exceeded")
        retry=row["retries"]+(1 if action=="retry" else 0)
        if retry>row["retry_limit"]:raise LifecycleError("retry limit exceeded")
        executor=row["executor"]
        if action=="start":
            executor=actor
        if action=="accept":
            if actor==executor:raise LifecycleError("executor cannot self-accept")
            if verified is not True or not row["head_sha"]:
                raise LifecycleError("requires independent GitHub attestation at a head SHA")
        if action=="review":
            if not isinstance(head_sha,str) or not re.fullmatch(r"[0-9a-f]{40}",head_sha):
                raise LifecycleError("review needs exact commit SHA")
        if action=="retry":
            executor=None
        next_sha=head_sha if action=="review" else row["head_sha"]
        db.execute("UPDATE tasks SET state=?,rev=?,spent=?,retries=?,executor=?,head_sha=? WHERE id=?",
                   (state,expected+1,row["spent"]+spend,retry,executor,next_sha,id))
        db.execute("INSERT INTO events(task,revision,action,actor,details) VALUES (?,?,?,?,?)",
                   (id,expected+1,action,actor,json.dumps({"cost_cents":spend,"head_sha":head_sha})))
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK");raise
    return show(db,id)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db",type=Path,default=DEFAULT_DB)
    sub=p.add_subparsers(dest="action",required=True)
    c=sub.add_parser("create")
    c.add_argument("id");c.add_argument("--issue",type=int,required=True)
    c.add_argument("--criteria",required=True);c.add_argument("--budget-cents",type=int,default=0)
    c.add_argument("--retry-limit",type=int,default=2)
    v=sub.add_parser("show");v.add_argument("id")
    t=sub.add_parser("transition")
    t.add_argument("id");t.add_argument("event",choices=sorted({k for m in STEPS.values() for k in m}))
    t.add_argument("--actor",required=True);t.add_argument("--expected-revision",required=True,type=int)
    t.add_argument("--cost-cents",type=int,default=0);t.add_argument("--head-sha")
    t.add_argument("--repo");t.add_argument("--pr",type=int)
    args=p.parse_args()
    try:
        with connect(args.db) as db:
            if args.action=="create":result=create(db,args.id,args.issue,args.criteria,args.budget_cents,args.retry_limit)
            elif args.action=="show":result=show(db,args.id)
            else:
                verified=False
                if args.event=="accept":
                    if not args.repo or not args.pr:raise LifecycleError("accept needs --repo and --pr")
                    try:
                        from scripts import attest
                    except ModuleNotFoundError:
                        import attest
                    report=attest.inspect(args.repo,args.pr,set(attest.DEFAULT_REQUIRED))
                    snapshot=show(db,args.id)
                    if report["head_sha"]!=snapshot["head_sha"]:
                        raise LifecycleError("attested PR head differs from task review head")
                    verified=True
                result=transition(db,args.id,args.event,args.actor,args.expected_revision,
                                  args.cost_cents,args.head_sha,verified)
            print(json.dumps(result,indent=2))
    except (LifecycleError,sqlite3.Error,OSError,ValueError) as e:
        print("lifecycle: "+str(e),file=sys.stderr);raise SystemExit(1)
if __name__=="__main__":main()
