#!/usr/bin/env python3
import importlib.util
import json
import shutil
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks={'Python >=3.11':sys.version_info>=(3,11),'Git installed':shutil.which('git') is not None,
        'jsonschema installed':importlib.util.find_spec('jsonschema') is not None}
for name,ready in checks.items(): print(('OK: ' if ready else 'MISSING: ')+name)
j=json.loads((root/'config/project.json').read_text())
print('Project initialized:',j.get('initialized'))
sys.exit(0 if all(checks.values()) else 1)
