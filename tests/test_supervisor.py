"""Real subprocess supervision, cancellation and recovery tests with fake CLIs."""
import json
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import lifecycle, supervisor

ROOT=Path(__file__).resolve().parents[1]
SIMPLE="import sys;data=sys.stdin.read();print('fixture response', len(data))"
SLOW="import sys,time;sys.stdin.read();time.sleep(10)"

class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.dbpath=Path(self.tmp.name)/"tasks.sqlite3"
        self.db=lifecycle.connect(self.dbpath)
        lifecycle.create(self.db,"fixture-"+str(id(self)),42,
                         "The fixture agent process must finish with real logs",200,2)
        self.task=self.db.execute("SELECT id FROM tasks").fetchone()[0]
        lifecycle.transition(self.db,self.task,"ready","owner",0)
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def runtime(self,script):
        return (patch.object(supervisor,"safe_branch",return_value="feature/fixture"),
                patch.object(supervisor,"shutil_which",return_value=sys.executable),
                patch.object(supervisor.harness,"command",
                             return_value=[sys.executable,"-c",script]))
    def enter(self,patches):
        for p in patches:self.addCleanup(p.stop);p.start()
    def test_dry_run_does_not_charge_or_mutate(self):
        self.enter(self.runtime(SIMPLE))
        r=supervisor.run(self.db,self.task,"codex","engineer","worker",
                         reserve_cents=50,root=ROOT)
        self.assertEqual(r["status"],"dry-run")
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"ready")
        self.assertEqual(lifecycle.show(self.db,self.task)["spent"],0)
    def test_refuses_unmetered_execution_without_ack(self):
        self.enter(self.runtime(SIMPLE))
        with self.assertRaisesRegex(supervisor.SupervisorError,"ack-unmetered"):
            supervisor.run(self.db,self.task,"codex","engineer","worker",root=ROOT,
                           reserve_cents=50,execute=True)
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"ready")
    def test_live_fake_process_to_verification(self):
        self.enter(self.runtime(SIMPLE))
        r=supervisor.run(self.db,self.task,"codex","engineer","worker",
                         root=ROOT,reserve_cents=50,execute=True,ack_unmetered=True)
        self.assertEqual(r["status"],"verifying")
        self.assertEqual(r["exit_code"],0)
        self.assertIn("stdout_sha256",r)
        self.assertNotIn("stdout",r)
        actual=lifecycle.show(self.db,self.task)
        self.assertEqual(actual["state"],"verifying")
        self.assertEqual(actual["spent"],50)
        self.assertEqual(supervisor.previous(self.db,self.task)["status"],"verifying")
    def test_process_failure_transitions_and_allows_manual_retry(self):
        self.enter(self.runtime("import sys;sys.stdin.read();sys.exit(9)"))
        r=supervisor.run(self.db,self.task,"claude","engineer","worker",
                         root=ROOT,reserve_cents=30,execute=True,ack_unmetered=True)
        self.assertEqual(r["exit_code"],9)
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"failed")
        current=lifecycle.show(self.db,self.task)
        lifecycle.transition(self.db,self.task,"retry","owner",current["rev"])
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"ready")
    def test_real_child_cancellation(self):
        self.enter(self.runtime(SLOW))
        outcome=[]
        def worker():
            with lifecycle.connect(self.dbpath) as separate:
                outcome.append(supervisor.run(separate,self.task,"hermes","engineer","worker",
                                root=ROOT,reserve_cents=30,execute=True,ack_unmetered=True,
                                timeout=20))
        thread=threading.Thread(target=worker)
        thread.start()
        deadline=time.monotonic()+8
        while lifecycle.show(self.db,self.task)["state"]!="running" and time.monotonic()<deadline:
            time.sleep(0.03)
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"running")
        snapshot=lifecycle.show(self.db,self.task)
        lifecycle.transition(self.db,self.task,"cancel","owner",snapshot["rev"])
        thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcome[0]["status"],"cancelled")
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"cancelled")
    def test_stale_lease_can_be_recovered(self):
        row=lifecycle.show(self.db,self.task)
        started=lifecycle.transition(self.db,self.task,"start","worker",row["rev"])
        supervisor.init(self.db)
        self.db.execute("INSERT INTO attempts(task,revision,harness,actor,worker_pid,agent_pid,heartbeat,status) VALUES (?,?,?,?,?,?,?,?)",
                        (self.task,started["rev"],"codex","worker",91234567,91234568,time.time()-1000,"running"))
        recovered=supervisor.recover(self.db,self.task,"owner",120,
                                     process_alive=lambda pid: False)
        self.assertEqual(recovered["state"],"failed")
        self.assertEqual(supervisor.previous(self.db,self.task)["status"],"interrupted")
    def test_live_process_cannot_be_recovered(self):
        started=lifecycle.transition(self.db,self.task,"start","worker",1)
        supervisor.init(self.db)
        self.db.execute("INSERT INTO attempts(task,revision,harness,actor,worker_pid,agent_pid,heartbeat,status) VALUES (?,?,?,?,?,?,?,?)",
                        (self.task,started["rev"],"codex","worker",91234567,91234568,time.time()-1000,"running"))
        with self.assertRaisesRegex(supervisor.SupervisorError,"still alive"):
            supervisor.recover(self.db,self.task,"owner",120,
                               process_alive=lambda pid: pid==91234568)
    def test_claude_provider_reported_billing(self):
        import json
        self.enter(self.runtime("import sys,json;sys.stdin.read();print(json.dumps({'total_cost_usd':0.12}))"))
        result=supervisor.run(self.db,self.task,"claude","engineer","worker",root=ROOT,
                              reserve_cents=50,execute=True,ack_unmetered=True)
        self.assertEqual(result["provider_reported_cost_cents"],12)
        self.assertEqual(result["status"],"verifying")

    def test_cost_overrun_rejects_verification(self):
        self.enter(self.runtime("import sys,json;sys.stdin.read();print(json.dumps({'total_cost_usd':0.5}))"))
        result=supervisor.run(self.db,self.task,"claude","engineer","worker",root=ROOT,
                              reserve_cents=10,execute=True,ack_unmetered=True)
        self.assertEqual(result["status"],"budget-overrun")
        self.assertEqual(lifecycle.show(self.db,self.task)["state"],"failed")

    def test_output_limit_terminates_run(self):
        self.enter(self.runtime("import sys;sys.stdin.read();print('X'*2000)"))
        with patch.object(supervisor,"MAX_OUTPUT_BYTES",1000):
            result=supervisor.run(self.db,self.task,"codex","engineer","worker",root=ROOT,
                                  reserve_cents=20,execute=True,ack_unmetered=True)
        self.assertEqual(result["status"],"output-limit")

    def test_refuses_dirty_checkout(self):
        from subprocess import CompletedProcess
        fake=[CompletedProcess([],0,"feature/work\n",""),CompletedProcess([],0," M app.py\n","")]
        with patch.object(supervisor.subprocess,"run",side_effect=fake):
            with self.assertRaisesRegex(supervisor.SupervisorError,"uncommitted"):
                supervisor.safe_branch(ROOT)

    def test_refuses_to_mutate_default_branch(self):
        with patch.object(supervisor.subprocess,"run",return_value=type("R",(),{"returncode":0,"stdout":"main\n"})()):
            with self.assertRaisesRegex(supervisor.SupervisorError,"default branch"):
                supervisor.safe_branch(ROOT)

if __name__=="__main__":unittest.main()
