# Supervised agent execution

Open ASS now joins the task lifecycle and the Hermes/Codex/Claude CLI adapters through `python3 scripts/openass.py run`. Run one ready task using:

```bash
python3 scripts/openass.py task create issue-42 --issue 42 --criteria "The feature meets the accepted acceptance tests" --budget-cents 500
python3 scripts/openass.py task transition issue-42 ready --actor owner --expected-revision 0
python3 scripts/openass.py run run issue-42 --harness codex --role engineer --actor worker --reserve-cents 100
python3 scripts/openass.py run run issue-42 --harness codex --role engineer --actor worker --reserve-cents 100 --execute --ack-unmetered
```

The command is dry-run-first. Paid inference requires explicit `--execute --ack-unmetered`. The worker refuses `main` and `master` and any dirty working tree, uses the runtime's isolated worktree/sandbox flags, hashes stdout/stderr to private untracked `.openass/runs/`, records the PID and heartbeat, and moves a successful attempt to **verifying**. This is not acceptance: tests, reviewer and GitHub attestation remain separate. Cancellation stops the subprocess, and `run recover` handles dead stale leases while refusing to duplicate live work. Failed tasks may be manually retried within the task's retry limit.

**Cost limitation:** `--reserve-cents` consumes a portion of the task's **allocation** before a call. It is neither a provider billing measurement nor a hard limit imposed on the model provider. Claude Code now receives its native `--max-budget-usd` limit, while provider-reported JSON cost is parsed when available; overruns fail acceptance. Codex/Hermes may lack a reliable dollar cap, so the operator must still explicitly acknowledge unmetered execution. Unknown reported cost remains null, not zero. Set billing limits, token limits and sandbox policies in the underlying provider/harness; never depend on Open ASS's SQLite ledger alone.

**Permissions limitation:** Noninteractive Hermes may bypass approval prompts. A sandbox with actual restricted filesystem/network access is mandatory for sensitive execution. The command generator never adds `--yolo` or bypasses Claude/Codex permissions. Agent tool output is untrusted and must not be treated as evidence of verified success.

**Isolation:** A locally chosen Git branch does not mean the process is container-isolated. The host is responsible for isolating files, secrets and network; a Git worktree only isolates a checkout. Use separate credentials for executor and authorized reviewer.

**Privacy:** Raw stdout/stderr are capped at 5 MB each per attempt and stored locally under `.openass/runs/` with restrictive file modes and aren't echoed to the console. They may still contain data supplied by the provider; secure and periodically purge this ignored directory.

The fixtures in `tests/test_supervisor.py` run actual child processes, including cancellation and interruption recovery. Authenticated live model execution requires the operator's existing CLI credentials and remains opt-in.

### v0.5 crash and stdin guarantees

The state transition to `running`, budget reservation, durable event and attempt lease are now a **single SQLite IMMEDIATE transaction**; the task cannot be left running without a recoverable attempt if insertion fails. The agent prompt is fed by a monitored background writer so an unresponsive child cannot block timeout/cancellation. Crash recovery still requires a stale lease and no live local PID, and assumes the same host/process namespace; cross-host orphan recovery remains a separate orchestrator concern.

### OCI execution boundary (v0.5)

Choose `--backend container --container-image REGISTRY/IMAGE@sha256:DIGEST` on `openass run run`. The Docker command is built as an argv array, refuses tag-only images, uses `--pull=never`, drops all capabilities, disables networking, runs as the invoking nonroot uid/gid, and exposes only the selected workspace as a writable mount. No Docker socket, home directory, SSH agent, credentials or network is mounted. The image must be **pre-pulled** and must contain the specific agent CLI; this offline security profile cannot access hosted inference APIs. Online execution requires an independently secured egress/broker policy—do not flip to unrestricted bridge networking. Docker is not a VM security boundary and access to the Docker daemon is privileged. The older `--backend local` remains available for authorized environments; it has no host filesystem isolation.

CI also exercises a real ephemeral Docker container: nonroot UID, isolated workspace, absent outside secret, loopback-only networking, and scratch storage. The fixture resolves a test image's immutable digest after pull. Production agent images must be pre-pulled and digest pinned.
