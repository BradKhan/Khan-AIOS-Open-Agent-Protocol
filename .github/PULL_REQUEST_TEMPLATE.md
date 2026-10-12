# Proposed change

Issue: #13

Risk: critical
Verification: Unit tests, risk policy gate and independent GitHub CI.
Security review: Framework changes reviewed for writable MCP exposure, shell injection, unpinned Actions, unsafe hooks, role privilege escalation and PR policy bypass. A GitHub ruleset with human approval is still required.

## Outcome and changes

What user-observable behavior changed? What did not?

## Risk class

Explicit declaration above is parsed by `scripts/pr_gate.py`; the risk is also computed from sensitive paths.

## Verification evidence

- Head commit SHA:
- Exact test commands and exit codes:
- CI run URL at current head:
- Acceptance criteria addressed:
- Negative and regression cases:
- Not verified / known limitations:

## Review and approval

Independently reviewed by:
Critical-change approval and rollback plan, if applicable:

An agent cannot approve its own PR. Configure GitHub rulesets and human reviewers.
