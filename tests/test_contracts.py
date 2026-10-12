import copy
import json
import unittest
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[1]

class ContractTests(unittest.TestCase):
    def fixture(self,kind):
        return (json.loads((ROOT/'contracts'/f'{kind}.schema.json').read_text()),
                json.loads((ROOT/'examples'/f'{kind}.json').read_text()))
    def test_task_valid(self):
        schema,obj=self.fixture('task')
        jsonschema.validate(obj,schema)
    def test_evidence_valid(self):
        schema,obj=self.fixture('evidence')
        jsonschema.validate(obj,schema,format_checker=jsonschema.FormatChecker())
    def test_task_rejects_missing_acceptance(self):
        schema,obj=self.fixture('task')
        obj['acceptance']=[]
        with self.assertRaises(jsonschema.ValidationError): jsonschema.validate(obj,schema)
    def test_task_rejects_bad_risk(self):
        schema,obj=self.fixture('task')
        obj['risk']='none'
        with self.assertRaises(jsonschema.ValidationError): jsonschema.validate(obj,schema)
    def test_task_rejects_policy_bypass(self):
        schema,obj=self.fixture('task')
        obj['disable_ci']=True
        with self.assertRaises(jsonschema.ValidationError): jsonschema.validate(obj,schema)
    def test_evidence_needs_commit_sha(self):
        schema,obj=self.fixture('evidence')
        del obj['commit_sha']
        with self.assertRaises(jsonschema.ValidationError): jsonschema.validate(obj,schema)
    def test_bad_evidence_url(self):
        schema,obj=self.fixture('evidence')
        obj['checks'][0]['artifact_url']='bad uri with spaces'
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(obj,schema,format_checker=jsonschema.FormatChecker())
if __name__=='__main__':unittest.main()
