# Open ASS evaluation suite — executable, with limits

Run `python3 scripts/openass.py bench plan` or `bench self-test`. The manifest `evaluations/tasks.json` includes **18 independent coding problems** (text, data, logic, money arithmetic, path/credential safety) and at least 54 acceptance cases. The agent workspace receives only `solution.py`, `TASK.md` and optional Open ASS guidance; acceptance inputs and expected answers stay in the controller. The evaluation script validates actual runnable Python outputs rather than accepting agent narratives.

```bash
python3 scripts/openass.py bench plan
python3 scripts/openass.py bench self-test
# Example authenticated and billable evaluation; use your own pre-pulled pinned verifier image
python3 scripts/openass.py bench run --mode baseline --harness codex --model-version YOUR_VERSION --image registry/py@sha256:YOUR_DIGEST --execute --ack-paid-local-agent --out baseline.json
python3 scripts/openass.py bench run --mode openass --harness codex --model-version YOUR_VERSION --image registry/py@sha256:YOUR_DIGEST --execute --ack-paid-local-agent --out openass.json
python3 scripts/openass.py bench compare --baseline baseline.json --openass openass.json
```

Live runs require locally installed, authenticated agent CLIs. The local model invocation is **not host-sandboxed** by the evaluator and requires explicit acknowledgment. Agent-generated code is verified only in the existing offline Docker boundary using the supplied pinned image with Python installed. For strict safety, run the *entire model execution* under an external VM/sandbox with scoped credentials.

The comparison fails when harness, model version, task IDs or starting source hash differ. It reports actual accepted tasks and elapsed time. Cost stays null unless sourced from trusted provider usage telemetry, which this iteration does not implement; it does not invent cost/quality improvements. Do not generalize 18 synthetic tasks into performance on real customer projects. Expand with held-out, non-public projects and repeated model runs before making marketing claims.

Self-tests exercise a correct solution, a broken starter, validation isolation, inconsistent model comparisons and forbidden mutable Docker images without spending model tokens. No paid agent runs were initiated in CI.
