"""Container command boundary tests: no inherited secrets or network by default."""
import tempfile
import unittest
from pathlib import Path
from scripts import sandbox

IMAGE="registry.example.org/agents/openass@sha256:"+("a"*64)

class SandboxTests(unittest.TestCase):
    def test_digest_pinned_offline_container(self):
        with tempfile.TemporaryDirectory() as folder:
            args=sandbox.wrap(["codex","exec","-"],folder,IMAGE,uid=1000,gid=1000)
        self.assertEqual(args[0:3],["docker","run","--rm"])
        self.assertIn("--network=none",args)
        self.assertIn("--read-only",args)
        self.assertIn("--cap-drop=ALL",args)
        self.assertIn("--security-opt=no-new-privileges",args)
        self.assertIn("--pull=never",args)
        self.assertIn("--user",args)
        self.assertEqual(args[args.index("--user")+1],"1000:1000")
        self.assertEqual(args[-4:],[IMAGE,"codex","exec","-"])
        self.assertNotIn("--privileged",args)
        self.assertNotIn("/var/run/docker.sock"," ".join(args))
        self.assertNotIn("/home"," ".join(args))
    def test_refuse_mutable_tag(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(sandbox.SandboxError,"digest-pinned"):
                sandbox.wrap(["python3"],folder,"python:latest",uid=1000,gid=1000)
    def test_refuse_root_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(sandbox.SandboxError,"nonroot"):
                sandbox.wrap(["python3"],folder,IMAGE,uid=0,gid=0)
    def test_refuse_workspace_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"link").symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(sandbox.SandboxError,"non-symlink"):
                sandbox.wrap(["python3"],root/"link",IMAGE,uid=1000,gid=1000)
    def test_refuse_unknown_argv(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(sandbox.SandboxError):
                sandbox.wrap("sh -c pwd",folder,IMAGE,uid=1000,gid=1000)
