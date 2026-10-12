#!/usr/bin/env python3
"""Run template contracts and real configured app checks. Fail closed when absent."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def fail(message):
    raise RuntimeError(message)

def run(argv, name):
    if not isinstance(argv, list) or not argv or not all(isinstance(x,str) and x for x in argv):
        fail(name + ': expected nonempty argv array, not a shell string')
    print('[verify] '+name+': '+repr(argv), flush=True)
    result = subprocess.run(argv, cwd=ROOT, check=False)
    if result.returncode:
        fail(name+': exit code '+str(result.returncode))

def verify_contracts():
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError('Install requirements-dev.txt') from exc
    required = ['AGENTS.md','PROJECT.md','ARCHITECTURE.md','POLICY.md',
                'sops/fast.md','sops/standard.md','sops/critical.md',
                '.github/PULL_REQUEST_TEMPLATE.md','docs/architecture.md']
    for item in required:
        file = ROOT / item
        if not file.is_file() or not file.read_text().strip():
            fail('Required file missing or empty: '+item)
    for kind in ('task','evidence'):
        schema = json.loads((ROOT/'contracts'/f'{kind}.schema.json').read_text())
        fixture = json.loads((ROOT/'examples'/f'{kind}.json').read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(fixture,schema,format_checker=jsonschema.FormatChecker())
    run([sys.executable, 'scripts/context.py', 'check'], 'ICM context routing')
    run([sys.executable, 'scripts/skills.py', 'check'], 'pinned skill catalog')
    run([sys.executable, 'scripts/agents.py', 'check'], 'specialist role registry')
    run([sys.executable, 'scripts/security_baseline.py'], 'framework static security')
    print('[verify] documentation and schemas PASS')

def detected_source():
    result=[]
    for name in ('package.json','pyproject.toml','go.mod','Cargo.toml','pom.xml'):
        if (ROOT/name).is_file(): result.append(name)
    for folder in ('src','app','server','worker','packages'):
        path=ROOT/folder
        if path.exists() and any(f.is_file() for f in path.rglob('*')):
            result.append(folder)
    for extension in (".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go"):
        for file in ROOT.glob("*" + extension):
            if file.is_file():
                result.append(file.name)
    for name in ("index.html", "Dockerfile", "Makefile", "requirements.txt"):
        if (ROOT / name).is_file():
            result.append(name)
    return sorted(set(result))

def verify_application(config):
    if not isinstance(config.get('initialized'),bool):
        fail('initialized must be boolean')
    v=config.get('verification')
    if not isinstance(v,dict):
        fail('verification config missing')
    if not config['initialized']:
        if detected_source():
            fail('Application source found in uninitialized template mode')
        if v.get('application_command'):
            fail('Cannot configure app tests in template mode; initialize first')
        print('[verify] TEMPLATE ONLY: application behavior NOT VERIFIED')
        return
    if config.get('assurance_tier') not in ('fast','standard','critical'):
        fail('Invalid assurance tier')
    project=(ROOT/'PROJECT.md').read_text()
    if any(x in project for x in ('[Project name]','[Whose problem?]','[Concrete problem]','[User-observable result]')):
        fail('Fill in PROJECT.md before application verification')
    architecture=(ROOT/'ARCHITECTURE.md').read_text()
    if any(x in architecture for x in ('[External systems and responsibilities]', '[What runs where and why]', '[APIs, schemas, events, integrations]')):
        fail('Fill in ARCHITECTURE.md before application verification')
    command=v.get('application_command')
    if not command: fail('Application verification command missing')
    run(command,'application')
    security=v.get('security_command')
    if security: run(security,'security')
    elif config['assurance_tier']=='critical':
        fail('Critical assurance tier requires security command')
    else: print('[verify] Security coverage NOT VERIFIED (no security command configured)')

def main():
    verify_contracts()
    run([sys.executable,'-m','unittest','discover','-s','tests','-v'],'contract tests')
    config=json.loads((ROOT/'config/project.json').read_text())
    verify_application(config)
    print('[verify] TEMPLATE SELF-TEST ONLY' if not config['initialized'] else '[verify] Configured application checks passed; review other obligations separately')

if __name__=='__main__':
    try: main()
    except (RuntimeError,ValueError,OSError,KeyError,json.JSONDecodeError) as exc:
        print('[verify] FAILED: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
