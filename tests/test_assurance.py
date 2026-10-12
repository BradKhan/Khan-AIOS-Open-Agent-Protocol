import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import verify

class AssuranceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)
        (self.path/'PROJECT.md').write_text('Name: Fixture\nUsers: Operators\nProblem: Validation\nOutcome: Verified build\n')
        (self.path/'ARCHITECTURE.md').write_text('Context: Test backend\nComponents and boundaries: Local app\nInterfaces: HTTP\n')
        self.p=patch.object(verify,'ROOT',self.path)
        self.p.start()
    def tearDown(self):
        self.p.stop()
        self.temp.cleanup()
    def config(self,tier='standard'):
        return {'initialized':True,'assurance_tier':tier,
                'verification':{'application_command':['python3','-c','pass'],'security_command':None}}
    def test_missing_application_tests_fails(self):
        j=self.config()
        j['verification']['application_command']=None
        with self.assertRaisesRegex(RuntimeError,'missing'): verify.verify_application(j)
    def test_critical_security_fails(self):
        with patch.object(verify,'run'):
            with self.assertRaisesRegex(RuntimeError,'requires security'): verify.verify_application(self.config('critical'))
    def test_template_rejects_source(self):
        (self.path/'src').mkdir()
        (self.path/'src'/'app.py').write_text('pass')
        with self.assertRaisesRegex(RuntimeError,'source'): verify.verify_application({'initialized':False,'verification':{}})
    def test_template_rejects_root_level_code(self):
        (self.path/'app.py').write_text('print("application")')
        with self.assertRaisesRegex(RuntimeError,'source'):
            verify.verify_application({'initialized':False,'verification':{}})

    def test_application_requires_architecture(self):
        (self.path/'ARCHITECTURE.md').write_text('Context: [External systems and responsibilities]')
        with patch.object(verify,'run'):
            with self.assertRaisesRegex(RuntimeError,'ARCHITECTURE.md'):
                verify.verify_application(self.config())

    def test_shell_string_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'argv array'):
            verify.run('echo ok; rm -rf /','bad input')
    def test_nonzero_exit_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'exit code 7'):
            verify.run(['python3','-c','import sys;sys.exit(7)'],'bad check')
if __name__=='__main__':unittest.main()
