# Release stage

## Inputs
- Accepted PR, verified commit SHA, required approvals and applicable release policy.
- Release notes, migrations, rollback plan, and relevant `release` references.

## Process
- Confirm current-head CI and approval states from GitHub, not agent testimony.
- Run production-readiness checks; rehearse rollback for critical changes.
- Deploy only with the required authorization and bounded credentials.

## Outputs
- Immutable release reference, deployment evidence, rollback instructions, monitoring results.
- Document follow-up defects as separate GitHub issues.

## Permissions
- Never infer deployment approval from completion of development.
- Sensitive production actions require explicit authorized approval.

## References
- Load only the canonical files listed in `context/routes.json`.
