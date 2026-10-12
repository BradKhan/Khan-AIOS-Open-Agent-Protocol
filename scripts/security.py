#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
j=json.loads((root/'config/project.json').read_text())
cmd=j.get('verification',{}).get('security_command')
if not cmd or not isinstance(cmd,list) or not all(isinstance(x,str) and x for x in cmd):
    raise SystemExit('Security check not configured as argv array')
raise SystemExit(subprocess.run(cmd,cwd=root,check=False).returncode)
