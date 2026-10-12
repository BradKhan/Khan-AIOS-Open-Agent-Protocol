"""Realistic but hermetic GitHub attestation tests."""
import unittest

from scripts import attest


SHA = "a"*40
RUN = {"head_sha": SHA, "name": "template-contracts", "status": "completed", "conclusion": "success"}
GATE = {"head_sha": SHA, "name": "pr-risk", "status": "completed", "conclusion": "success"}
PR = {"state": "open", "number": 14, "head": {"sha": SHA}, "user": {"login": "implementer"}}
REV = [{"state":"APPROVED","commit_id":SHA,"submitted_at":"2026-10-12T18:00:00Z","user":{"login":"reviewer"}}]


class AttestTests(unittest.TestCase):
    def test_accepts_real_checks_and_independent_current_head_review(self):
        report = attest.evaluate(PR, [RUN, GATE], REV, {"template-contracts","pr-risk"})
        self.assertEqual(report["current_head_approvers"],["reviewer"])

    def test_rejects_missing_check(self):
        with self.assertRaisesRegex(attest.AttestError,"required checks"):
            attest.evaluate(PR,[RUN],REV,{"template-contracts","pr-risk"})

    def test_rejects_failed_check(self):
        with self.assertRaisesRegex(attest.AttestError,"required checks"):
            attest.evaluate(PR,[dict(RUN,conclusion="failure"),GATE],REV,{"template-contracts","pr-risk"})

    def test_rejects_stale_check(self):
        with self.assertRaisesRegex(attest.AttestError,"required checks"):
            attest.evaluate(PR,[dict(RUN,head_sha="b"*40),GATE],REV,{"template-contracts","pr-risk"})

    def test_rejects_self_approval(self):
        self_review=[dict(REV[0],user={"login":"implementer"})]
        with self.assertRaisesRegex(attest.AttestError,"human approval"):
            attest.evaluate(PR,[RUN,GATE],self_review,{"template-contracts","pr-risk"})

    def test_rejects_approval_on_outdated_head(self):
        stale=[dict(REV[0],commit_id="b"*40)]
        with self.assertRaisesRegex(attest.AttestError,"human approval"):
            attest.evaluate(PR,[RUN,GATE],stale,{"template-contracts","pr-risk"})

    def test_later_changes_requested_cancels_approval(self):
        reviews=REV+[{"state":"CHANGES_REQUESTED","commit_id":SHA,"submitted_at":"2026-10-12T19:00:00Z","user":{"login":"reviewer"}}]
        with self.assertRaisesRegex(attest.AttestError,"human approval"):
            attest.evaluate(PR,[RUN,GATE],reviews,{"template-contracts","pr-risk"})

    def test_missing_check_run_pages_fail_closed(self):
        def mocked(path):
            if path.endswith("/pulls/14"):
                return PR
            if "check-runs" in path:
                return {"total_count": 101, "check_runs": [RUN,GATE]}
            return REV
        with self.assertRaisesRegex(attest.AttestError,"paginated"):
            attest.inspect("BradKhan/open-ASS",14,{"template-contracts","pr-risk"},fetch=mocked)

    def test_invalid_repo_is_rejected_before_api_access(self):
        with self.assertRaisesRegex(attest.AttestError,"invalid repository"):
            attest.inspect("../../secret",14,set(),fetch=lambda x: None)

    def test_observation_only_mode_explicit(self):
        self.assertEqual(attest.evaluate(PR,[RUN,GATE],[],{"template-contracts","pr-risk"},False)["current_head_approvers"],[])


if __name__ == "__main__":
    unittest.main()
