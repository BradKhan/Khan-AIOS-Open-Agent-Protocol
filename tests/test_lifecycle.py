"""Transactional lifecycle invariants: actual on-disk recovery and contention."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from scripts import lifecycle

SHA="f"*40
class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"state.sqlite3"
        self.db=lifecycle.connect(self.path)
        lifecycle.create(self.db,"task-1",42,"Acceptance criteria are written down",150,1)
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def move(self,event,revision,actor="owner",**kw):
        return lifecycle.transition(self.db,"task-1",event,actor,revision,**kw)
    def test_recover_from_actual_disk(self):
        self.move("ready",0)
        self.db.close()
        self.db=lifecycle.connect(self.path)
        self.assertEqual(lifecycle.show(self.db,"task-1")["state"],"ready")
        self.assertEqual(len(lifecycle.show(self.db,"task-1")["events"]),2)
    def test_stale_revision_rejected(self):
        self.move("ready",0)
        with self.assertRaisesRegex(lifecycle.LifecycleError,"stale"):
            self.move("start",0,"engineer")
    def test_independent_connections_cannot_overwrite(self):
        other=lifecycle.connect(self.path)
        try:
            self.move("ready",0)
            with self.assertRaisesRegex(lifecycle.LifecycleError,"stale"):
                lifecycle.transition(other,"task-1","cancel","owner",0)
        finally:other.close()
    def test_retry_budget_bounded(self):
        self.move("ready",0);self.move("start",1,"engineer",spend=80)
        self.move("fail",2,"engineer")
        self.move("retry",3)
        self.move("start",4,"engineer",spend=70)
        with self.assertRaisesRegex(lifecycle.LifecycleError,"budget"):
            self.move("fail",5,spend=1)
        self.move("fail",5)
        with self.assertRaisesRegex(lifecycle.LifecycleError,"retry limit"):
            self.move("retry",6)
    def test_accept_requires_independent_attestation(self):
        self.move("ready",0);self.move("start",1,"executor")
        self.move("verify",2,"executor")
        self.move("review",3,"qa",head_sha=SHA)
        with self.assertRaisesRegex(lifecycle.LifecycleError,"self-accept"):
            self.move("accept",4,"executor",verified=True)
        with self.assertRaisesRegex(lifecycle.LifecycleError,"attestation"):
            self.move("accept",4,"owner")
        final=self.move("accept",4,"reviewer",verified=True)
        self.assertEqual(final["state"],"accepted")
        self.assertEqual(final["head_sha"],SHA)
    def test_cancel_irreversible(self):
        self.move("cancel",0)
        with self.assertRaisesRegex(lifecycle.LifecycleError,"invalid state"):
            self.move("ready",1)
    def test_duplicate_task_rejected(self):
        with self.assertRaisesRegex(lifecycle.LifecycleError,"already exists"):
            lifecycle.create(self.db,"task-1",42,"Expected behavior confirmed")
    def test_rollbacks_do_not_append_events(self):
        with self.assertRaisesRegex(lifecycle.LifecycleError,"invalid state"):
            self.move("verify",0)
        self.assertEqual(len(lifecycle.show(self.db,"task-1")["events"]),1)
    def test_reject_budget_and_identifier(self):
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.create(self.db,"../escape",1,"Acceptance criteria are clear",5)
        with self.assertRaises(lifecycle.LifecycleError):
            lifecycle.create(self.db,"task-2",1,"Acceptance criteria are clear",-1)
if __name__=="__main__":unittest.main()
