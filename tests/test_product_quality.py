"""Product-quality negative fixtures; no claims of autonomous design evaluation."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts import product_quality as q
class QualityTests(unittest.TestCase):
    def test_valid_semantic_html(self):
        html='<!doctype html><html lang="en"><head><title>App</title></head><body><h1>App</h1><label for="q">Query</label><input id="q"><img src="x.png" alt=""><button>Go</button></body></html>'
        self.assertTrue(q.inspect_html(html)["passed"])
    def test_inaccessible_form_and_images_rejected(self):
        html='<html><head><title>App</title></head><body><h1>App</h1><img src="x"><input><button></button></body></html>'
        report=q.inspect_html(html)
        self.assertFalse(report["passed"])
        self.assertGreaterEqual(len(report["errors"]),4)
    def test_generic_copy_detected_as_warning(self):
        html='<html lang="en"><title>T</title><h1>Unlock the power of magic</h1></html>'
        report=q.inspect_html(html)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["warnings"]),1)
    def test_external_link_security(self):
        html='<html lang="en"><title>T</title><h1>H</h1><a target="_blank" href="https://x">X</a></html>'
        self.assertFalse(q.inspect_html(html)["passed"])
    def test_plan_has_browser_and_copy_review(self):
        r=q.quality_plan()
        self.assertIn("browser-accessibility",[x["step"] for x in r["stages"]])
        self.assertIn("humanizer",[x.get("skill") for x in r["stages"]])
    def test_artifact_attestation_and_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            values={"browser.json":json.dumps({"passed":True,"checks":["route loads"]}).encode(),
                    "accessibility.json":json.dumps({"violations":[],"passes":["aria-label"]}).encode(),
                    "screen.png":q.PNG+b"pixel-data"}
            kinds={"browser.json":"browser","accessibility.json":"accessibility","screen.png":"screenshot"}
            for n,data in values.items():(root/n).write_bytes(data)
            artifacts=[{"kind":kinds[n],"path":n,"sha256":hashlib.sha256(raw).hexdigest()}
                       for n,raw in values.items()]
            document={"head_sha":"a"*40,"test_exit":0,"artifacts":artifacts,
                      "copy_review":{"reviewed":True,"reviewer":"editor"}}
            self.assertEqual(q.verify_evidence(document,root)["status"],"evidence-validated")
            (root/"screen.png").write_bytes(b"tampered")
            with self.assertRaisesRegex(q.QualityError,"checksum"):
                q.verify_evidence(document,root)
    def test_evidence_missing_real_browser_and_a11y_reports(self):
        with self.assertRaisesRegex(q.QualityError,"evidence"):
            q.verify_evidence({"head_sha":"a"*40,"test_exit":0,"artifacts":[]})
    def test_missing_copy_review_rejected(self):
        with self.assertRaises(q.QualityError):
            q.verify_evidence({"head_sha":"a"*40,"test_exit":0,"artifacts":[{}, {}, {}]})
if __name__=="__main__":unittest.main()
