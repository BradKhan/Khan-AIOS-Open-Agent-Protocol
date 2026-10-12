doctor:
    python3 scripts/doctor.py

verify:
    python3 scripts/verify.py

test:
    python3 -m unittest discover -s tests -v

security:
    python3 scripts/security.py

contract-task:
    python3 scripts/validate_artifact.py task examples/task.json

contract-evidence:
    python3 scripts/validate_artifact.py evidence examples/evidence.json

doctor-all:
    python3 scripts/openass.py doctor

roles:
    python3 scripts/agents.py list

mcp-check:
    python3 -m unittest tests.test_operational.MCPTests -v

security-baseline:
    python3 scripts/security_baseline.py

hooks-status:
    python3 scripts/openass.py hooks status
