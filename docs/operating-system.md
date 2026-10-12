# Operating Open ASS

Open ASS provides a working **engineering control plane in a GitHub repository**. It is not a coding model, a cloud orchestrator, or a promise that all third-party agents behave identically.

| Capability | Command | Actually implemented |
| --- | --- | --- |
| Diagnostics | `python3 scripts/openass.py doctor` | Checks dependencies, schemas, roles, context, skills, and framework security |
| Context | `python3 scripts/openass.py context plan implement --working examples/task.json` | Selected in-repository paths and exact SHA-256 hashes |
| Specialist handoffs | `python3 scripts/openass.py agents plan designer` | Role, stage, capabilities, installed skills and scoped context |
| Skills | `python3 scripts/openass.py skills install --profile core --profile web` | 17 pinned text instruction bundles, authenticated by Git blob hashes |
| Read-only MCP | `python3 scripts/openass.py mcp serve` | Stdio server exposing role, context and skill metadata |
| Git hooks | `python3 scripts/openass.py hooks install` | Explicit opt-in local checks, never sufficient for branch protection |
| PR policy | `python3 scripts/openass.py pr-check --event event.json` | PR risk declaration and escalation for sensitive files |
| Security baseline | `python3 scripts/openass.py security` | Framework AST and GitHub workflow checks; not app vulnerability scanning |
| Application checks | `python3 scripts/openass.py verify` | Runs configured app commands when initialized |
| PR attestation | `python3 scripts/openass.py attest --repo OWNER/REPO --pr 123` | Independent GitHub API check of head SHA, CI results, current-head human approval |

## Development cycle

An issue holds accepted criteria. Classify its risk, prepare scoped agent context, work in an isolated branch, and run the app's actual tests. Submit a PR. A read-only ordinary-PR job runs the PR risk checker from the trusted base commit, fetching the proposed commit **only as Git data**. It inspects risk declarations and sensitive changed paths without executing PR code. Rulesets still have to require this check. Independent review and required checks determine acceptance. The executor does not approve its own work.

### Hooks

Opt-in `.githooks/pre-commit` checks framework routing, skill integrity, roles and static security; `pre-push` additionally runs `verify.py`. An existing custom hooks directory is never replaced. Local hooks can be bypassed: GitHub rulesets are the enforcement boundary.

### Scoped, consumable context bundles

Run `python3 scripts/openass.py agents bundle engineer --working examples/task.json --max-bytes 64000` to emit the actual selected UTF-8 context with source hashes as JSON. Include a role-approved, installed skill only when needed: `--include-skill systematic-debugging`. The command fails rather than silently truncating a byte budget. It does not give the model new authority; verify all task files and skill instructions against policy. Avoid logging bundles containing private project material in public CI.

### Roles and skills

Nine roles are defined under `config/agents.json`; Claude Code project role files live under `.claude/agents/`. `agents plan` produces a context handoff and marks missing skills; it does not execute agents or grant authorization. The 17 upstream skill packages are opt-in, version-pinned **text**, not full runnable toolchains.

### MCP

The built-in stdio server exposes only `openass_context_plan`, `openass_agent_plan` and `openass_skill_profiles`. It has no shell, arbitrary file read, GitHub write or network tool. Host tool permissions still matter. Other MCP services (GitHub, browser, docs, memory) should be connected deliberately with scoped credentials.

### Public repository PR checks

The policy job uses ordinary `pull_request` and checks out the trusted base commit before evaluating PR metadata and changed paths. It has only read access and never executes proposed application code. This avoids the elevated `pull_request_target` event and GitHub's November 2026 event restrictions.

**Important:** the PR author can still edit the proposed workflow definition in their branch. Enforcement needs GitHub rulesets, independent review of workflow changes, and organization-required workflows where available. PR body risk declarations are not equivalent to owner approval.

### GitHub owner actions

Set **Template repository** on. Add appropriate topics. Set a default-branch ruleset to require `template-contracts` and `pr-risk` plus application checks, at least one authorized independent reviewer, review dismissal on updates, and restricted bypass/force-push rights. This configuration cannot be imposed by a copied repository or the current GitHub connector.

### Known gaps that cannot be papered over

- GitHub risk declaration checks can inspect filenames and PR text; human assessment is needed for behavioral risk. Branch protection must enforce actual reviews.
- The attest tool queries GitHub; semantic correctness, browser acceptance, security and deployment still require real tests and authorized reviewers.
- Installed skill instructions may need separately installed executables. Their text is untrusted data until vetted.
- Native Hermes/Codex execution, Paperclip orchestration, memory sync and comparative performance claims need real runtime evidence. See `docs/benchmarks.md`.

Do not claim the template's self-test verifies downstream application behavior.
