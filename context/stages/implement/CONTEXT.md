# Implementation stage

## Inputs
- Approved issue/spec and plan, exact base commit, bounded task scope.
- Canonical references for `implement`; only necessary prior-stage artifacts.

## Process
- Work in an isolated branch/worktree. Use applicable TDD and debugging skills.
- Run configured tests. Do not silently broaden scope or edit acceptance criteria.
- Revisit `specify` through a reviewed change if approved requirements cannot be met.

## Outputs
- Scoped commits, a PR linked to the issue, and actual test results.
- Hand off PR head SHA and reproducible commands to `verify`.

## Permissions
- Modify permitted workspace files and submit PRs.
- No self-approval, production changes, bypassed checks, or expanded credentials.

## References
- Use the exact paths declared in `context/routes.json`.
