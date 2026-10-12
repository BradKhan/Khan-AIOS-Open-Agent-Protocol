"""Owner-controlled GitHub administration plan, safe apply, and zero auto-write."""
import unittest
from unittest.mock import Mock
from scripts import github_admin as admin

REPO="BradKhan/open-ASS"
META={"full_name":REPO,"default_branch":"main","is_template":False,"topics":[]}

class AdminTests(unittest.TestCase):
    def test_produces_enforceable_rules_no_bypass(self):
        plan=admin.plan(REPO,META,[])
        rules=plan["changes"]["ruleset"]
        self.assertEqual(rules["enforcement"],"active")
        self.assertEqual(rules["bypass_actors"],[])
        checks=next(r for r in rules["rules"] if r["type"]=="required_status_checks")
        self.assertTrue(checks["parameters"]["strict_required_status_checks_policy"])
        self.assertEqual({c["context"] for c in checks["parameters"]["required_status_checks"]},
                         set(admin.CHECKS))
        self.assertTrue(all(c["integration_id"]==15368 for c in checks["parameters"]["required_status_checks"]))
        review=next(r for r in rules["rules"] if r["type"]=="pull_request")["parameters"]
        self.assertEqual(review["required_approving_review_count"],1)
        self.assertTrue(review["require_last_push_approval"])
        self.assertTrue(review["dismiss_stale_reviews_on_push"])
        self.assertFalse(review["require_code_owner_review"]) # solo owner would deadlock
    def test_default_preview_has_no_side_effect(self):
        p=admin.plan(REPO,META,[])
        self.assertTrue(p["changes"]["enable_template"])
        self.assertEqual(p["changes"]["ruleset_action"],"create")
        self.assertNotIn("owner-unsafe",p["changes"]["topics"])
    def test_apply_is_explicit_and_only_touches_owned_ruleset(self):
        p=admin.plan(REPO,META,[])
        calls=[]
        def fake(method,path,body=None,token=None):
            calls.append((method,path,body,token))
            return {"id":1}
        result=admin.apply(REPO,p,"secure-token",request=fake)
        self.assertEqual([x[0] for x in calls],["PATCH","PUT","POST"])
        self.assertTrue(calls[0][2]["is_template"])
        self.assertTrue(calls[2][1].endswith("/rulesets"))
        self.assertTrue(all(x[3]=="secure-token" for x in calls))
        self.assertEqual(len(result),3)
    def test_existing_ruleset_updates_by_id(self):
        p=admin.plan(REPO,dict(META,is_template=True),
                     [{"name":admin.RULESET_NAME,"id":42}])
        self.assertEqual(p["changes"]["ruleset_action"],"update")
        calls=[]
        admin.apply(REPO,p,"token",request=lambda *a,**kw:calls.append((a,kw)))
        self.assertEqual(calls[-1][0][0],"PUT")
        self.assertTrue(calls[-1][0][1].endswith("/rulesets/42"))
    def test_reject_wrong_repository(self):
        with self.assertRaises(admin.AdminError):
            admin.plan(REPO,dict(META,full_name="intruder/evil"),[])
    def test_dont_confuse_codeowner_review_with_available_review(self):
        enabled=admin.plan(REPO,META,[],require_codeowners=True)
        self.assertTrue(enabled["changes"]["ruleset"]["rules"][-1]["parameters"]["require_code_owner_review"])
    def test_reject_unauthenticated_write(self):
        with self.assertRaisesRegex(admin.AdminError,"token"):
            admin.github_api("POST","/repos/BradKhan/open-ASS/rulesets",{},token=None)
    def test_reject_arbitrary_api_urls(self):
        with self.assertRaises(admin.AdminError):
            admin.github_api("GET","/user/emails")

if __name__=="__main__":
    unittest.main()
