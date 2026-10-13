"""Actual Docker isolation fixture for CI; no paid inference or secrets."""
import os
import subprocess
import tempfile
from pathlib import Path
from scripts import sandbox

def main():
    image=os.environ.get("OPENASS_TEST_IMAGE")
    if not image:
        raise RuntimeError("digest-resolved OPENASS_TEST_IMAGE required")
    with tempfile.TemporaryDirectory(prefix="openass-oci-") as folder:
        root=Path(folder)
        workspace=root/"workspace"
        workspace.mkdir()
        (root/"private-marker").write_text("host-only")
        command=["sh","-c",
                 "test \"$(id -u)\" -ne 0 && "
                 "test -d /workspace && "
                 "test ! -e /workspace/../private-marker && "
                 "test \"$(ls /sys/class/net | grep -v '^lo$' | wc -l)\" -eq 0 && "
                 "printf isolated > /workspace/proof && touch /tmp/scratch"]
        argv=sandbox.wrap(command,workspace,image)
        result=subprocess.run(argv,capture_output=True,text=True,timeout=90,check=False)
        if result.returncode:
            raise RuntimeError("OCI boundary failed: "+result.stderr[-2500:])
        if (workspace/"proof").read_text()!="isolated":
            raise RuntimeError("OCI fixture output mismatch")
    print("Real Docker nonroot/offline/workspace-only boundary PASS")

if __name__=="__main__":
    main()
