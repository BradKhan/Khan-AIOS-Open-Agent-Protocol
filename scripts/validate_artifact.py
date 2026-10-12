#!/usr/bin/env python3
"""Only syntax validation; this does not attest execution evidence."""
import argparse
import json
from pathlib import Path
import jsonschema
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('kind',choices=('task','evidence'))
p.add_argument('file',type=Path)
a=p.parse_args()
schema=json.loads((root/'contracts'/f'{a.kind}.schema.json').read_text())
jsonschema.Draft202012Validator.check_schema(schema)
jsonschema.validate(json.loads(a.file.read_text()),schema,format_checker=jsonschema.FormatChecker())
print('Contract valid. Content not independently attested.')
