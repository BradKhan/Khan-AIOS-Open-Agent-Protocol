#!/usr/bin/env python3
"""Check installed CLI flags against Open ASS's real subprocess adapters.

--help and --version only. No AI inference, login, changes or network calls.
"""
import argparse
import re
import shutil
import subprocess
import sys

# Anthropic intentionally omits --max-turns from --help while keeping it
# supported for -p. A help-only probe must not flag this documented behavior.
FLAGS={
    "codex":("exec",("--sandbox","--json")),
    "claude":(None,("--output-format","--permission-mode")),
    "hermes":("chat",("--query-file","--oneshot","--format",
                     "--max-turns","--worktree","--checkpoints","--toolsets"))
}

def probe(name,runner=subprocess.run,locator=shutil.which,expected_version=None):
    if name not in FLAGS:raise ValueError("unknown harness")
    exe=locator(name)
    if not exe:return {"harness":name,"status":"missing","missing":["executable"]}
    sub,required=FLAGS[name]
    help_cmd=[exe]+([sub] if sub else [])+["--help"]
    version_cmd=[exe,"--version"]
    try:
        help_out=runner(help_cmd,text=True,capture_output=True,timeout=20,check=False)
        version_out=runner(version_cmd,text=True,capture_output=True,timeout=20,check=False)
    except (OSError,subprocess.TimeoutExpired) as ex:
        return {"harness":name,"status":"error","message":type(ex).__name__}
    full=(help_out.stdout or "")+(help_out.stderr or "")
    version=((version_out.stdout or "")+(version_out.stderr or "")).strip()[:250]
    missing=[flag for flag in required if flag not in full]
    if help_out.returncode!=0:missing.append("successful --help")
    if version_out.returncode!=0:missing.append("successful --version")
    if expected_version is not None and expected_version not in version:
        missing.append("version "+expected_version)
    return {"harness":name,"status":"pass" if not missing else "incompatible",
            "version":version,"missing":missing,
            "note":"CLI option compatibility only; no paid inference or sandbox assertion."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--harness",action="append",choices=tuple(FLAGS))
    p.add_argument("--expect-version",action="append",default=[],help="name=version")
    p.add_argument("--strict",action="store_true")
    a=p.parse_args()
    expected={}
    for entry in a.expect_version:
        if "=" not in entry:p.error("expected name=version")
        name,version=entry.split("=",1)
        if name not in FLAGS or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}",version):
            p.error("invalid expected version")
        expected[name]=version
    names=a.harness or list(FLAGS)
    results=[probe(name,expected_version=expected.get(name)) for name in names]
    import json
    print(json.dumps(results,indent=2))
    if a.strict and any(result["status"]!="pass" for result in results):
        raise SystemExit(1)
if __name__=="__main__":
    main()
