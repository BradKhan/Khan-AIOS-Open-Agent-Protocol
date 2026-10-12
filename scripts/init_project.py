#!/usr/bin/env python3
"""Explicitly initialize a copied template with real verification commands."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--name',required=True)
    p.add_argument('--tier',choices=('fast','standard','critical'),default='standard')
    p.add_argument('--app-check',nargs='+',required=True)
    p.add_argument('--security-check',nargs='+')
    a=p.parse_args()
    if a.tier=='critical' and not a.security_check: p.error('critical tier requires --security-check')
    f=ROOT/'config/project.json'
    j=json.loads(f.read_text())
    if j['initialized']: p.error('project already initialized')
    j.update(initialized=True,project_name=a.name,assurance_tier=a.tier)
    j['verification']={'application_command':a.app_check,'security_command':a.security_check}
    f.write_text(json.dumps(j,indent=2)+'\n')
    print('Configured checks. Replace placeholders and run python3 scripts/verify.py.')
if __name__=='__main__': main()
