#!/usr/bin/env python3
"""Opt-in authenticated coding smoke test in a disposable git repository.

Only a successful file assertion counts. Never touches the current source tree,
opens PRs, changes GitHub settings, or claims host-level process isolation.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from scripts import harness
except ModuleNotFoundError:
    import harness

PROOF="OPEN_ASS_AGENT_PASS\n"
TASK=("Create proof.txt in the working directory. It must contain exactly one "
      "line: OPEN_ASS_AGENT_PASS followed by a newline. Do not modify other "
      "files. Do not commit, push, deploy, read secrets or call remote services.")

class LiveSmokeError(ValueError):pass

def prepare(folder,runner=subprocess.run):
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"AGENTS.md").write_text(
        "# Disposable Open ASS test\nOnly modify proof.txt as specified in the prompt.\n")
    (folder/"acceptance.txt").write_text("proof.txt must be exactly OPEN_ASS_AGENT_PASS plus newline.\n")
    cmds=(
      ["git","init","-q","-b","smoke"],
      ["git","add","AGENTS.md","acceptance.txt"],
      ["git","-c","user.name=Open ASS fixture","-c","user.email=fixture@example.invalid",
       "commit","-q","-m","isolated fixture"]
    )
    for cmd in cmds:
        result=runner(cmd,cwd=folder,capture_output=True,text=True,timeout=15,check=False)
        if result.returncode:
            raise LiveSmokeError("temporary Git checkout setup failed")

def plan(runtime,budget_cents=100):
    if runtime not in harness.HARNESSES:raise LiveSmokeError("unsupported harness")
    if type(budget_cents)!=int or not 1<=budget_cents<=10000:
        raise LiveSmokeError("live smoke budget must be 1..10000 cents")
    argv=harness.command(runtime,"write-branch",budget_cents=budget_cents)
    if runtime=="claude":
        argv+=["--permission-mode","acceptEdits"]
    if runtime=="hermes":
        # The disposable repository is already isolated as a test artifact.
        # Hermes worktree mode would put proof.txt in a different checkout.
        argv=[arg for arg in argv if arg!="--worktree"]
        argv+=["--run-budget","120"]
    return argv

def git_state(folder):
    """Exact revision and tracked/untracked changes in a disposable fixture."""
    head=subprocess.run(["git","rev-parse","HEAD"],cwd=folder,check=False,
                        capture_output=True,text=True,timeout=10)
    status=subprocess.run(["git","status","--porcelain","--untracked-files=all"],
                          cwd=folder,check=False,capture_output=True,text=True,timeout=10)
    if head.returncode or status.returncode or len(head.stdout.strip())!=40:
        raise LiveSmokeError("could not inspect disposable Git state")
    return head.stdout.strip(),status.stdout.splitlines()


def smoke(runtime,budget_cents=100,timeout=180,execute=False,
          ack_runtime_permissions=False,runner=None):
    argv=plan(runtime,budget_cents)
    if not execute:
        return {"status":"dry-run","harness":runtime,"argv":argv,
                "warning":"Real execution requires --execute --ack-runtime-permissions; may incur charges"}
    if not ack_runtime_permissions:
        raise LiveSmokeError("pass --ack-runtime-permissions for an authenticated agent run")
    if not shutil.which(argv[0]):
        raise LiveSmokeError("harness binary missing: "+argv[0])
    if type(timeout)!=int or not 10<=timeout<=600:
        raise LiveSmokeError("timeout must be 10..600 seconds")
    runner=runner or harness.execute
    with tempfile.TemporaryDirectory(prefix="openass-agent-smoke-") as work:
        root=Path(work)
        prepare(root)
        baseline_head,baseline_status=git_state(root)
        if baseline_status:
            raise LiveSmokeError("disposable checkout was dirty before the agent started")
        result=runner(argv,TASK,root=root,timeout=timeout)
        proof=root/"proof.txt"
        observed=(proof.read_bytes() if proof.is_file() and not proof.is_symlink() else b"")
        final_head,changed=git_state(root)
        clean_scope=(final_head==baseline_head and changed==["?? proof.txt"])
        passed=(result["exit_code"]==0 and observed==PROOF.encode("utf-8") and clean_scope)
        return {"status":"pass" if passed else "failed",
                "harness":runtime,"exit_code":result["exit_code"],
                "git_head_unchanged":final_head==baseline_head,
                "only_expected_file_changed":clean_scope,
                "observed_changes":changed[:20],
                "proof_sha256":hashlib.sha256(observed).hexdigest() if observed else None,
                "expected_sha256":hashlib.sha256(PROOF.encode()).hexdigest(),
                "elapsed_time_reported":result.get("elapsed_seconds"),
                "limits":"Disposable git checkout, not an OS sandbox. CLI credentials required. No GitHub acceptance or deployment."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--harness",required=True,choices=tuple(harness.HARNESSES))
    p.add_argument("--budget-cents",type=int,default=100)
    p.add_argument("--timeout",type=int,default=180)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--ack-runtime-permissions",action="store_true")
    a=p.parse_args()
    try:
        output=smoke(a.harness,a.budget_cents,a.timeout,a.execute,a.ack_runtime_permissions)
        print(json.dumps(output,indent=2))
        if output["status"]=="failed":raise SystemExit(1)
    except (LiveSmokeError,harness.HarnessError,OSError,ValueError,subprocess.TimeoutExpired) as ex:
        print("live-smoke: "+str(ex),file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":main()
