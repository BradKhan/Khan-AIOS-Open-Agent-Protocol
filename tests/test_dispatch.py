"""Task dispatch: real lifecycle transitions with injected executor and GitHub evidence."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts import dispatch, lifecycle

SHA="a"*40
ROOT=Path(__file__).resolve().parents[1]

class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=lifecycle.connect(Path(self.temp.name)/"task.sqlite")
        self.task="dispatch-fixture"
        lifecycle.create(self.db,self.task,42,"All required behavior must be tested",500,2)
        lifecycle.transition(self.db,self.task,"ready","owner",0)
    def tearDown(self):
        self.db.close();self.temp.cleanup()
    def success(self,db,id,runtime,role,actor,**kw):
        self.assertEqual(role,"engineer")
        self.assertIsInstance(kw.get("include_skills",[]),list)
        self.assertTrue(kw["execute"])
        self.assertTrue(kw["ack_unmetered"])
        initial=lifecycle.show(db,id)
        next_=lifecycle.transition(db,id,"start",actor,initial["rev"],spend=kw["reserve_cents"])
        lifecycle.transition(db,id,"verify",actor,next_["rev"])
        return {"status":"verifying","exit_code":0,"provider_reported_cost_cents":None}
    def failure(self,db,id,runtime,role,actor,**kw):
        initial=lifecycle.show(db,id)
        next_=lifecycle.transition(db,id,"start",actor,initial["rev"],spend=kw["reserve_cents"])
        lifecycle.transition(db,id,"fail",actor,next_["rev"])
        return {"status":"failed","exit_code":9}
    def verify(self,root):
        self.assertTrue(root.is_dir())
        return {"exit_code":0,"output_sha256":"f"*64}

    def verified_head(self,root,head,verifier):
        return {"exit_code":0,"output_sha256":"f"*64,"head_sha":head}
    def test_detached_revision_verifier_rejects_dirty_test_results(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            commands=[
                ["git","init","-q","-b","feature"],
                ["git","-c","user.name=fixture","-c","user.email=fixture@example.invalid",
                 "commit","--allow-empty","-qm","start"]
            ]
            for cmd in commands:
                p=subprocess.run(cmd,cwd=root,check=False,capture_output=True)
                self.assertEqual(p.returncode,0,p.stderr)
            head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
            def clean(root):
                self.assertNotEqual(root,Path(td))
                return {"exit_code":0,"output_sha256":"f"*64}
            r=dispatch.verify_revision(root,head,verifier=clean)
            self.assertEqual(r["head_sha"],head)
            def dirty(root):
                (root/"tampered.py").write_text("changed")
                return {"exit_code":0}
            with self.assertRaisesRegex(dispatch.DispatchError,"verification changed"):
                dispatch.verify_revision(root,head,verifier=dirty)

    def test_revision_handoff_rejects_unbound_evidence(self):
        self.success(self.db,self.task,"codex","engineer","worker",reserve_cents=20,
                     execute=True,ack_unmetered=True)
        with patch.object(dispatch,"local_head",return_value=SHA):
            with self.assertRaisesRegex(dispatch.DispatchError,"does not match"):
                dispatch.dispatch(self.db,self.task,"codex","worker",repo="BradKhan/open-ASS",pr=25,
                    execute=True,ack_unmetered=True,
                    verifier=self.verify,
                    commit_verifier=lambda root,head,verifier:{"exit_code":0,"head_sha":"b"*40},
                    fetch_pr=lambda repo,number,sha:{"head_sha":sha})
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"verifying")

    def test_dry_run_does_not_mutate_or_spawn(self):
        r=dispatch.dispatch(self.db,self.task,"codex","worker",reserve_cents=100)
        self.assertEqual(r["status"],"dry-run")
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"ready")
    def test_explicit_billing_acknowledgement(self):
        with self.assertRaisesRegex(dispatch.DispatchError,"ack-unmetered"):
            dispatch.dispatch(self.db,self.task,"codex","worker",reserve_cents=100,
                              execute=True,execute_agent=self.success)
    def test_success_requires_actual_app_verification(self):
        r=dispatch.dispatch(self.db,self.task,"codex","worker",reserve_cents=100,
                            execute=True,ack_unmetered=True,execute_agent=self.success,
                            verifier=self.verify)
        self.assertEqual(r["status"],"awaiting-pull-request")
        self.assertEqual(r["verification"]["exit_code"],0)
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"verifying")
        self.assertEqual(lifecycle.show(self.db,self.task)["spent"],100)
    def test_successful_pr_handoff_has_no_auto_approval(self):
        dispatch.dispatch(self.db,self.task,"codex","worker",reserve_cents=100,
                          execute=True,ack_unmetered=True,execute_agent=self.success,
                          verifier=self.verify)
        with patch.object(dispatch,"local_head",return_value=SHA):
            r=dispatch.dispatch(self.db,self.task,"codex","worker",repo="BradKhan/open-ASS",
                                pr=25,execute=True,ack_unmetered=True,
                                verifier=self.verify,commit_verifier=self.verified_head,
                                fetch_pr=lambda repo,number,sha:
                                    {"number":number,"head_sha":sha,"url":"https://github.com/BradKhan/open-ASS/pull/25"})
        self.assertEqual(r["status"],"awaiting-independent-review")
        self.assertEqual(r["head_sha"],SHA)
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"review")
        self.assertEqual(lifecycle.show(self.db,self.task)["head_sha"],SHA)
    def test_failure_preserves_state_without_fake_acceptance(self):
        r=dispatch.dispatch(self.db,self.task,"claude","worker",execute=True,
                            ack_unmetered=True,reserve_cents=20,
                            execute_agent=self.failure,verifier=self.verify)
        self.assertEqual(r["status"],"failed")
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"failed")
    def test_failure_then_retry_then_success(self):
        calls=[]
        def mixed(*args,**kwargs):
            calls.append(1)
            return self.failure(*args,**kwargs) if len(calls)==1 else self.success(*args,**kwargs)
        r=dispatch.dispatch(self.db,self.task,"codex","worker",execute=True,
                            ack_unmetered=True,reserve_cents=30,
                            execute_agent=mixed,max_attempts=2,verifier=self.verify)
        self.assertEqual(r["status"],"awaiting-pull-request")
        self.assertEqual(len(r["attempts"]),2)
        self.assertEqual(lifecycle.show(self.db,self.task)["retries"],1)
    def test_retries_fully_exhausted(self):
        r=dispatch.dispatch(self.db,self.task,"codex","worker",execute=True,
                            ack_unmetered=True,reserve_cents=30,
                            execute_agent=self.failure,max_attempts=3,
                            verifier=self.verify)
        self.assertEqual(r["status"],"failed")
        self.assertEqual(len(r["attempts"]),3)
        self.assertEqual(lifecycle.show(self.db,self.task)["retries"],2)
    def test_invalid_retry_count_rejected(self):
        with self.assertRaises(dispatch.DispatchError):
            dispatch.dispatch(self.db,self.task,"codex","worker",max_attempts=0)
    def test_git_revision_mismatch_fails_closed(self):
        def fake(_):
            return {"state":"open","head":{"sha":"b"*40},
                    "base":{"repo":{"full_name":"BradKhan/open-ASS"}}}
        with self.assertRaisesRegex(dispatch.DispatchError,"head differs"):
            dispatch.matching_pr("BradKhan/open-ASS",5,SHA,fetch=fake)
    def test_git_cross_repo_fails_closed(self):
        def fake(_):
            return {"state":"open","head":{"sha":SHA},
                    "base":{"repo":{"full_name":"other/another"}}}
        with self.assertRaisesRegex(dispatch.DispatchError,"repository mismatch"):
            dispatch.matching_pr("BradKhan/open-ASS",5,SHA,fetch=fake)
    def test_dirty_git_checkout_rejected(self):
        runner=Mock(side_effect=[
            subprocess.CompletedProcess([],0,SHA+"\n",""),
            subprocess.CompletedProcess([],0," M src/app.py\n","")])
        with self.assertRaisesRegex(dispatch.DispatchError,"commit all work"):
            dispatch.local_head(ROOT,runner=runner)
    def test_real_application_required(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/"config").mkdir()
            (root/"config/project.json").write_text(json.dumps({"initialized":False}))
            with self.assertRaisesRegex(dispatch.DispatchError,"application checks"):
                dispatch.verify_project(root)
    def test_application_nonzero_exit_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/"config").mkdir()
            (root/"config/project.json").write_text(json.dumps({"initialized":True}))
            r=Mock(return_value=subprocess.CompletedProcess([],7,"","bad"))
            with self.assertRaisesRegex(dispatch.DispatchError,"exit 7"):
                dispatch.verify_project(root,runner=r)
    def test_application_success_reports_output_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/"config").mkdir()
            (root/"config/project.json").write_text(json.dumps({"initialized":True}))
            r=Mock(return_value=subprocess.CompletedProcess([],0,"passed",""))
            evidence=dispatch.verify_project(root,runner=r)
            self.assertEqual(evidence["exit_code"],0)
            self.assertEqual(len(evidence["output_sha256"]),64)

if __name__=="__main__":
    unittest.main()
