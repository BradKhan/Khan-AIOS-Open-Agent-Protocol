#!/usr/bin/env python3
"""Single source of truth for protected-branch CI and PR attestation.

The required job names in this file must match actual workflows. A mismatch is
an error, not a skipped check or a weaker release rule.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/release-gates.json"
class ReleasePolicyError(ValueError): pass

def read(path=POLICY, root=ROOT):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleasePolicyError("cannot load release-gates.json") from exc
    if not isinstance(data, dict) or set(data)!={"version","github_actions_app_id","checks"} or data["version"]!=1:
        raise ReleasePolicyError("invalid release policy schema")
    app=data["github_actions_app_id"]
    if type(app)!=int or app<=0:
        raise ReleasePolicyError("GitHub Actions app ID must be a positive integer")
    records=data["checks"]
    if not isinstance(records,list) or not 3<=len(records)<=30:
        raise ReleasePolicyError("required checks must be a bounded nonempty list")
    found=set()
    for item in records:
        if not isinstance(item,dict) or set(item)-{"name","workflow","job","matrix_version"} or not {"name","workflow","job"}<=set(item):
            raise ReleasePolicyError("invalid check definition")
        name,workflow,job=item["name"],item["workflow"],item["job"]
        if not isinstance(name,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 .()_/-]{0,120}",name):
            raise ReleasePolicyError("invalid required check name")
        if name in found:raise ReleasePolicyError("duplicate required check name: "+name)
        found.add(name)
        if not isinstance(workflow,str) or not re.fullmatch(r"\.github/workflows/[a-z0-9-]+\.yml",workflow):
            raise ReleasePolicyError("invalid workflow path")
        if not isinstance(job,str) or not re.fullmatch(r"[a-z][a-z0-9-]*",job):
            raise ReleasePolicyError("invalid workflow job key")
        matrix=item.get("matrix_version")
        if matrix is not None:
            if not isinstance(matrix,str) or not re.fullmatch(r"[0-9]+\.[0-9]+",matrix):
                raise ReleasePolicyError("invalid matrix version")
            if name!=f"{job} ({matrix})":
                raise ReleasePolicyError("matrix check name doesn't match job and version")
        elif name!=job:
            raise ReleasePolicyError("required name differs from nonmatrix job")
        file=root/workflow
        if file.is_symlink() or not file.is_file():
            raise ReleasePolicyError("workflow missing or symlinked: "+workflow)
        text=file.read_text(encoding="utf-8")
        if not re.search(r"(?m)^  "+re.escape(job)+r":\s*$",text):
            raise ReleasePolicyError("job does not exist in "+workflow+": "+job)
        if matrix is not None and not re.search(r"""['"]"""+re.escape(matrix)+r"""['"]""",text):
            raise ReleasePolicyError("matrix version absent from workflow: "+matrix)
        # A required check can never be path-filtered out on some PRs.
        lines = text.splitlines()
        pull_request_index = next((i for i, line in enumerate(lines)
                                   if line == "  pull_request:"), None)
        if pull_request_index is not None:
            for line in lines[pull_request_index + 1:]:
                if line and not line.startswith((" ", "#")):
                    break
                if line.startswith("  ") and not line.startswith(("   ", "#")):
                    break
                if re.match(r"^    paths(?:-ignore)?:\\s*$", line):
                    raise ReleasePolicyError("required workflow is path-filtered: " + workflow)
    return {"app_id":app,"checks":tuple(x["name"] for x in records)}

def main():
    try:
        result=read()
        print(json.dumps(result,indent=2))
    except ReleasePolicyError as exc:
        print("release-policy: "+str(exc),file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":
    main()
