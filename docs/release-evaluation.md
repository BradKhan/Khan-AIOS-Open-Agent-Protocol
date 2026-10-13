# Evaluation and release gates

Run python3 scripts/openass.py evaluate to exercise seven deterministic negative controls (credential context, traversal, destructive hook, critical PR risk, original owner leakage, inaccessible HTML, stale GitHub CI). It records observed pass/fail results and errors, not productivity scores.

The browser-evaluation CI job installs Playwright 1.60.0, real headless Chromium, and axe-core 4.10.3. It screenshots a valid fixture, runs WCAG 2A/AA automated accessibility rules, verifies artifact SHA-256 digests, and requires an intentionally defective fixture to fail. Browser packages remain optional for users copying the template.

For a real application, run browser --html APP --axe-js PATH --head-sha SHA to generate observations, then quality evidence MANIFEST to verify them. Copy-reviewer metadata supplied by a caller is not independent approval; GitHub reviews and branch rulesets are still authoritative.

Run readiness --repo OWNER/REPO --strict to inspect public GitHub metadata for template mode, topics and branch protection. This is an advisory owner settings check, never a substitute for checking exact required reviews and statuses.

Current evaluation cases exercise mechanical controls, not real agent productivity, design taste, or runtime sandbox enforcement. Reproducible comparative agent evaluations remain separate.

## v0.5 executable benchmark path

`scripts/verify.py` invokes `scripts/eval_suite.py self-test` after the unit suite. The self-test executes a trusted reference solution and confirms that the broken starter fails. Eighteen evaluation tasks and their 56 withheld-from-agent acceptance cases are in `evaluations/tasks.json`. The `bench run` command requires an explicit paid-run acknowledgment and a pre-pulled digest-pinned Docker verifier image. No model accuracy, latency or cost improvement can be claimed until comparable live baseline/Open ASS runs have actually been collected.
