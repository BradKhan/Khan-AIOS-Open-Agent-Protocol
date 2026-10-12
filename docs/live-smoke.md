# Authenticated agent capability smoke test

Open ASS contains a minimal, disposable **coding task test** for three agent CLIs. It is not the user's sample application and does not touch any existing project checkout. A fresh temporary Git repository is created and discarded after verifying an exact proof file; an agent's own "done" statement is insufficient.

```bash
python3 scripts/openass.py live-smoke --harness codex
python3 scripts/openass.py live-smoke --harness codex --budget-cents 100 --execute --ack-runtime-permissions
python3 scripts/openass.py live-smoke --harness claude --budget-cents 100 --execute --ack-runtime-permissions
python3 scripts/openass.py live-smoke --harness hermes --budget-cents 100 --execute --ack-runtime-permissions
```

Dry-run is the default. Real execution requires a locally installed, authenticated CLI and the explicit approval flags. Claude receives its `--max-budget-usd` setting. Hermes is bounded by its turn and wall-clock flags and the outer process timeout. Codex uses its own workspace-write sandbox. A disposable Git checkout is **not OS isolation**: execute in a container or VM when you need strict filesystem/network credential boundaries. Do not run under a privileged account.

Results include the actual exit code, exact SHA-256 of `proof.txt`, and whether its entire byte content matches the expected result. A model may refuse the task due to missing permissions; that is reported as a failure, never assumed successful. The command never pushes, opens PRs, deploys, or configures repository permissions. The user's provider usage is billed according to their provider plan, not GitHub CI.

CI tests this script's isolation, dry-run behavior, permission acknowledgment and acceptance logic with a fixture runner, **without** burning provider tokens. Authenticated comparisons across the user's own agent installations require those accounts to be connected locally, not shared with ChatGPT.
