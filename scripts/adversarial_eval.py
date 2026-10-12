#!/usr/bin/env python3
"""Repeatable internal failure-injection tests. Not a productivity benchmark."""
import argparse
import json
import tempfile
import time
from pathlib import Path

try:
    from scripts import attest, context, hermes_hook, pr_gate, project_setup, product_quality
except ModuleNotFoundError:
    import attest, context, hermes_hook, pr_gate, project_setup, product_quality

CASES=("context-secret","path-traversal","hook-destructive","pr-risk","owner-isolation",
       "broken-accessibility","stale-ci")
class EvaluationError(ValueError):pass

def run(case):
    if case=="context-secret":
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/".env").write_text("API_TOKEN=secret")
            try:context.confined_file(root,".env")
            except context.ContextError:return True
        return False
    if case=="path-traversal":
        with tempfile.TemporaryDirectory() as d:
            try:context.confined_file(Path(d),"../../etc/passwd")
            except context.ContextError:return True
        return False
    if case=="hook-destructive":
        result=hermes_hook.decision({"hook_event_name":"pre_tool_call","tool_name":"terminal",
            "tool_input":{"command":"git reset --hard HEAD"},"cwd":"/tmp"})
        return result.get("action")=="block"
    if case=="pr-risk":
        return pr_gate.required_risk(["scripts/verify.py"])=="critical"
    if case=="owner-isolation":
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/"config").mkdir();(root/".github").mkdir()
            (root/"config/project.json").write_text('{"initialized":false}')
            (root/".github/CODEOWNERS").write_text("* @BradKhan")
            changes=project_setup.build(root,"App","ActualOwner","standard",["pytest"])
            return "@BradKhan" not in changes[root/".github/CODEOWNERS"]
    if case=="broken-accessibility":
        return not product_quality.inspect_html(
            '<html><title>Bad</title><h1>App</h1><img src="x"><input></html>')["passed"]
    if case=="stale-ci":
        head="a"*40
        pull={"state":"open","head":{"sha":head},"user":{"login":"worker"}}
        checks=[{"head_sha":"b"*40,"name":"template-contracts","status":"completed","conclusion":"success"}]
        try:attest.evaluate(pull,checks,[],{"template-contracts"},False)
        except attest.AttestError:return True
        return False
    raise EvaluationError("unknown eval case: "+str(case))

def evaluate(cases=CASES):
    if len(cases)!=len(set(cases)) or any(c not in CASES for c in cases):
        raise EvaluationError("invalid or repeated evaluation cases")
    details=[]
    for name in cases:
        start=time.monotonic()
        try:passed=run(name);error=None
        except Exception as exc:passed=False;error=type(exc).__name__+": "+str(exc)
        details.append({"case":name,"passed":passed,"error":error,
                        "seconds":round(time.monotonic()-start,3)})
    return {"suite":"openass-adversarial-fixtures-v1","total":len(details),
            "passed":sum(1 for d in details if d["passed"]),"results":details,
            "limits":"Fixture controls, not autonomous agent quality, deployment security or productivity measurements"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    result=evaluate()
    text=json.dumps(result,indent=2)
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(text+"\n")
    print(text)
    if result["passed"]!=result["total"]:raise SystemExit(1)
if __name__=="__main__":main()
