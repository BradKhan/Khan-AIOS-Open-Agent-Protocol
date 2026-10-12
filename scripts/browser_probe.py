#!/usr/bin/env python3
"""Actual headless Chromium + axe-core QA of a local HTML document.

Browser and axe-core are explicit optional dependencies; no remote script injection.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class BrowserError(ValueError):pass

def probe(html,axe,out,head_sha,reviewer=None):
    if not re.fullmatch("[a-f0-9]{40}",head_sha):
        raise BrowserError("requires exact Git revision")
    if not html.is_file() or not axe.is_file():
        raise BrowserError("missing HTML or pinned local axe-core script")
    if not out.resolve().is_relative_to(ROOT.resolve()) or out.is_symlink():
        raise BrowserError("artifact directory escapes repository")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BrowserError("install optional playwright and browser binaries") from exc
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1280,"height":800})
        page.goto(html.resolve().as_uri(),wait_until="load",timeout=20000)
        title=page.title()
        headings=page.locator("h1").count()
        page.screenshot(path=str(out/"screen.png"),full_page=True)
        page.add_script_tag(content=axe.read_text(encoding="utf-8"))
        result=page.evaluate("""async () => {
          const report = await axe.run(document, {runOnly:{type:"tag",values:["wcag2a","wcag2aa"]}});
          return {violations:report.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length})),
                  passes:report.passes.map(v=>v.id),incomplete:report.incomplete.map(v=>v.id)};
        }""")
        browser.close()
    browser_result={"passed":bool(title and headings==1),"checks":[
        {"title":title,"h1_count":headings,"url":html.name}]}
    (out/"browser.json").write_text(json.dumps(browser_result,indent=2)+"\n")
    (out/"accessibility.json").write_text(json.dumps(result,indent=2)+"\n")
    artifacts=[]
    for name,kind in (("screen.png","screenshot"),("browser.json","browser"),
                      ("accessibility.json","accessibility")):
        path=out/name
        artifacts.append({"kind":kind,"path":path.relative_to(ROOT).as_posix(),
                          "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest={"head_sha":head_sha,"test_exit":0 if browser_result["passed"] and not result["violations"] else 1,
              "artifacts":artifacts,
              "copy_review":{"reviewed":bool(reviewer),"reviewer":reviewer or ""},
              "note":"Reviewer is caller-supplied; this does not attest independent approval."}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return {"browser":browser_result,"accessibility":result,
            "manifest":(out/"manifest.json").relative_to(ROOT).as_posix()}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--html",required=True,type=Path)
    p.add_argument("--axe-js",required=True,type=Path)
    p.add_argument("--out",type=Path,default=ROOT/".openass/quality")
    p.add_argument("--head-sha",required=True)
    p.add_argument("--copy-reviewer")
    a=p.parse_args()
    try:
        report=probe(a.html,a.axe_js,a.out,a.head_sha,a.copy_reviewer)
        print(json.dumps(report,indent=2))
        if not report["browser"]["passed"] or report["accessibility"]["violations"]:
            raise SystemExit(1)
    except (BrowserError,ValueError,OSError) as e:
        print("browser-probe: "+str(e),file=sys.stderr);raise SystemExit(1)
if __name__=="__main__":main()
