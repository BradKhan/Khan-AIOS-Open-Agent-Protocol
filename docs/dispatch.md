# Task dispatch: execution → application tests → PR handoff

The optional dispatcher joins the SQLite lifecycle and supervised agent runner into one explicit workflow. It can retry failed attempts within the task's existing retry and cost allocations, run **real configured application verification**, inspect an open PR at the exact local HEAD and transition the task to `review`.

It never creates a GitHub approval, pushes commits, merges, deploys, or certifies its own output. The PR must be created and pushed separately under authorized credentials.

Start from an initialized application checkout on a dedicated non-default branch with a clean working tree:

```bash
python3 scripts/openass.py task create issue-42 --issue 42 --criteria "The accepted behavior passes the configured application checks" --budget-cents 500
python3 scripts/openass.py task transition issue-42 ready --actor owner --expected-revision 0
python3 scripts/openass.py dispatch issue-42 --harness codex --actor worker --reserve-cents 100
python3 scripts/openass.py dispatch issue-42 --harness codex --actor worker --reserve-cents 100 --execute --ack-unmetered
```

The third command is **dry-run**. The fourth may incur inference charges; Claude receives a native `--max-budget-usd` option while other CLIs require explicit unmetered acknowledgement and their host billing controls. A successful agent subprocess changes a task to `verifying`, **not accepted**. Without a PR, the dispatcher runs `scripts/verify.py` in the working checkout as **preliminary** evidence, not acceptance. Once a PR is supplied, it tests a detached Git worktree at that precise commit, checks for verifier-induced modifications, then rechecks the PR head and local branch before permitting review. Independent protected GitHub CI remains authoritative: a malicious commit could modify its own test script, and a Git worktree is not an OS sandbox.

After committing work, opening a PR and pushing the exact reviewed commit, resume the same task with:

```bash
python3 scripts/openass.py dispatch issue-42 --harness codex --actor worker --repo OWNER/REPO --pr NUMBER --execute --ack-unmetered
```

This confirms the local HEAD and open PR head match and records a `review` handoff. Only a separately authorized reviewer and actual current-head GitHub checks can accept via the existing `task transition ... accept --repo ... --pr ...` command.

Failure is retained in SQLite with its event history, retry count and cost reservations. `--max-attempts` is limited to 1–3 in a single invocation, and the task's stronger cumulative retry and budget limits always apply. The dispatcher does not automatically turn a rejected verification into a new code run: fix the issue or explicitly return it to a ready/retry state.

**Boundaries:** Application checks run local commands supplied by the project owner. No shared hosted queue, remote locks, cloud credentials or authenticated billed cross-agent test is supplied. External tools need a real host sandbox; a Git branch alone is not filesystem isolation.

### Commit-bound handoff

The final PR handoff includes `verification.head_sha` equal to the tested Git commit. PR movement or local checkout movement during execution rejects the handoff. Tests operate in a detached temporary worktree of that exact SHA and may not modify the checkout. The test runner is still repository code and not intrinsically trusted: independent CI on the actual PR commit remains mandatory before acceptance.

### Adaptive role and skill routing

`openass activate --description "Design responsive dashboard" --path app/main.tsx` selects an implementation specialist, the installed role-declared skills, and required QA/review roles based on task text and changed file scope. The dispatcher uses the same deterministic selector by default. Missing external skills are reported, not silently pretended to be active; use `--strict-skills` to fail before inference if required skills are absent. `--working` supplies changed paths. Critical-risk paths add a security reviewer; these reviewers are required recommendations, **not** autonomously spawned or self-attested reviewers. Ambiguous acceptance criteria are paused for clarification instead of initiating a paid agent run. Selection does not override host permissions or GitHub approval.
