# Risk, permissions and acceptance policy

## Risk classes
- fast: bounded, reversible local change. Clear issue, checks, PR review.
- standard: feature or significant defect. Spec or acceptance contract, plan, tests and independent review.
- critical: authorization, payments, personal data, infrastructure, destructive changes or other high-impact work. Add threat review, negative tests, recovery plan and explicit owner approval.

Risk can be raised by any reviewer. Lowering risk requires owner approval recorded against the issue.

## Authorized actions
Agents may read code, edit isolated branches, run scoped tests and submit PRs. Agents may not disable required checks, change branch protections, alter approval roles, raise spending limits or approve their own work. Production deployment, irreversible actions and privilege changes require approval.

## Acceptance
Require an issue, testable criteria, current-head CI result, applicable independent review and authorized merge. Tests passing are necessary but do not prove UX or business correctness.

## Execution limits
Set budgets, retry ceilings and timeouts in real orchestration controls, not merely prompts. Use idempotent task claims, leases, unique run IDs and reconciliation to recover from interrupted execution.
