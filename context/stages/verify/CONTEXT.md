# Verification stage

## Inputs
- Accepted acceptance criteria, PR diff and head SHA, applicable test configuration.
- Reported evidence and canonical `verify` references.

## Process
- Run independent CI and domain-appropriate checks at the exact PR head SHA.
- Compare observed behavior against criteria and accepted specification.
- Distinguish self-reported outputs from independently attested CI results.
- Reopen implementation for failures; do not rewrite the criteria to pass.

## Outputs
- Review findings and links to actual CI runs, tests, and accepted evidence.
- Hand off only eligible, authorized changes to `release`.

## Permissions
- Reviewer may reject work; executor may not approve their own change.
- Do not disable required checks or merge without authorization.

## References
- Load from `context/routes.json` rather than copying policy content here.
