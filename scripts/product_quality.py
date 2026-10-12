#!/usr/bin/env python3
"""Web product quality checks and inspectable browser/accessibility evidence."""
import argparse
import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
try:
    from scripts import context
except ModuleNotFoundError:
    import context
ROOT=Path(__file__).resolve().parents[1]
PNG=b"\x89PNG\r\n\x1a\n"
class QualityError(ValueError):pass

class WebAudit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang=False;self.title=False;self.in_title=False;self.h1=0
        self.images=0;self.labels=set();self.fields=[];self.buttons=[];self.links=[]
        self.current=None;self.stack=[];self.errors=[]
    def handle_starttag(self,tag,raw):
        a=dict(raw);self.stack.append(tag)
        if tag=="html":self.lang=bool(a.get("lang","").strip())
        if tag=="title":self.in_title=True
        if tag=="h1":self.h1+=1
        if tag=="img":
            self.images+=1
            if "alt" not in a:self.errors.append("image missing alt attribute")
        if tag=="label" and a.get("for"):self.labels.add(a["for"])
        if tag in ("input","select","textarea") and a.get("type") not in ("hidden","submit"):
            self.fields.append((tag,a))
        if tag in ("button","a"):
            self.current={"kind":tag,"attrs":a,"text":[]}
            if tag=="a" and a.get("target")=="_blank":
                if not {"noopener","noreferrer"}<=set(a.get("rel","").split()):
                    self.errors.append("external target=_blank link missing noopener noreferrer")
    def handle_data(self,data):
        if self.in_title and data.strip():self.title=True
        if self.current:self.current["text"].append(data)
    def handle_endtag(self,tag):
        if tag=="title":self.in_title=False
        if self.current and tag==self.current["kind"]:
            if not "".join(self.current["text"]).strip() and not self.current["attrs"].get("aria-label"):
                self.errors.append(tag+" missing accessible name")
            if tag=="a" and not self.current["attrs"].get("href"):
                self.errors.append("anchor without href")
            self.current=None
        if tag in self.stack:self.stack.remove(tag)

def inspect_html(text):
    if not isinstance(text,str):raise QualityError("HTML must be UTF-8 text")
    audit=WebAudit()
    audit.feed(text)
    errors=list(audit.errors)
    if not audit.lang:errors.append("document html lang missing")
    if not audit.title:errors.append("document title missing")
    if audit.h1!=1:errors.append("expected exactly one h1")
    for tag,a in audit.fields:
        if not any((a.get("aria-label"),a.get("aria-labelledby"),
                    a.get("id") in audit.labels if a.get("id") else False)):
            errors.append(tag+" missing accessible label")
    warnings=[]
    for phrase in ("unlock the power of","revolutionize your","seamlessly integrate",
                   "cutting-edge solutions","elevate your experience"):
        if phrase in text.lower():warnings.append("review generic copy: "+phrase)
    return {"passed":not errors,"errors":errors,"warnings":warnings,
            "metrics":{"headings":audit.h1,"images":audit.images,"fields":len(audit.fields)}}

def quality_plan(profile="web"):
    if profile!="web":raise QualityError("unknown product profile")
    return {"profile":"web","stages":[
        {"step":"requirements","role":"architect","evidence":"accepted criteria"},
        {"step":"visual-direction","role":"designer","skill":"design-taste-frontend"},
        {"step":"implementation","role":"engineer","skill":"test-driven-development"},
        {"step":"design-review","role":"designer","skill":"impeccable"},
        {"step":"standards-review","role":"qa","skill":"web-design-guidelines"},
        {"step":"browser-accessibility","role":"qa","skill":"playwright-cli","evidence":"browser and axe results"},
        {"step":"copy-review","role":"writer","skill":"humanizer"},
        {"step":"independent-acceptance","role":"reviewer","evidence":"PR head and CI"}],
        "note":"Skills are recommendations; running them must yield independent observed evidence."}

def verify_evidence(document,root=ROOT):
    if not isinstance(document,dict):raise QualityError("evidence must be an object")
    if not re.fullmatch("[0-9a-f]{40}",str(document.get("head_sha",""))):
        raise QualityError("exact PR head SHA required")
    if type(document.get("test_exit"))!=int or document["test_exit"]!=0:
        raise QualityError("application tests did not pass")
    entries=document.get("artifacts")
    if not isinstance(entries,list) or len(entries)<3:
        raise QualityError("browser, accessibility, screenshot evidence required")
    required={"browser","accessibility","screenshot"}
    seen=set()
    for item in entries:
        if not isinstance(item,dict) or item.get("kind") not in required or item["kind"] in seen:
            raise QualityError("unknown or duplicate artifact kind")
        seen.add(item["kind"])
        path=context.confined_file(root,item.get("path"))
        content=path.read_bytes()
        digest=hashlib.sha256(content).hexdigest()
        if digest!=item.get("sha256") or not content:
            raise QualityError("artifact missing or checksum mismatch")
        if item["kind"]=="screenshot":
            if not content.startswith(PNG):raise QualityError("screenshot must be PNG")
        else:
            data=json.loads(content)
            if item["kind"]=="browser":
                if data.get("passed") is not True or not isinstance(data.get("checks"),list) or not data["checks"]:
                    raise QualityError("browser checks must report actual passing observations")
            if item["kind"]=="accessibility":
                if data.get("violations")!=[] or not isinstance(data.get("passes"),list) or not data["passes"]:
                    raise QualityError("accessibility report failed or empty")
    if seen!=required:raise QualityError("incomplete quality evidence")
    review=document.get("copy_review")
    if not isinstance(review,dict) or review.get("reviewed") is not True or not review.get("reviewer"):
        raise QualityError("copy review missing")
    return {"status":"evidence-validated","head_sha":document["head_sha"],
            "artifacts":len(seen),"warning":"Self-supplied files and hashes are not independent attestation."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("plan")
    h=sub.add_parser("html");h.add_argument("path")
    v=sub.add_parser("evidence");v.add_argument("path")
    a=p.parse_args()
    try:
        if a.command=="plan":result=quality_plan()
        elif a.command=="html":
            result=inspect_html(context.confined_file(ROOT,a.path).read_text(encoding="utf-8"))
        else:result=verify_evidence(json.loads(context.confined_file(ROOT,a.path).read_text()))
        print(json.dumps(result,indent=2))
        if a.command=="html" and not result["passed"]:raise SystemExit(1)
    except (QualityError,ValueError,OSError,context.ContextError) as ex:
        print("quality: "+str(ex),file=sys.stderr);raise SystemExit(1)
if __name__=="__main__":main()
