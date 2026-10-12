# Get your ASS running

From the repository root (Python 3.11+, Git):

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/openass.py doctor
python3 scripts/openass.py verify
python3 scripts/openass.py agents list
python3 scripts/openass.py skills list
```

Before initialization, **TEMPLATE SELF-TEST ONLY** is expected. That's not an application test.

Fill `PROJECT.md` and `ARCHITECTURE.md`, then configure a real application check. For an existing Node project:

```bash
python3 scripts/openass.py bootstrap --name my-app --owner YOUR_GITHUB_LOGIN --apply --app-check npm test
python3 scripts/openass.py verify
```

For critical projects supply a real `--security-check` command. PR risk is checked **per change** even when the project baseline is standard.

Install only useful skills:

```bash
python3 scripts/openass.py skills plan --profile core --profile web
python3 scripts/openass.py skills install --profile core --profile web
python3 scripts/openass.py agents plan designer
python3 scripts/openass.py agents bundle engineer --working examples/task.json --max-bytes 64000
```

Claude Code can use `.claude/agents/` and `.mcp.json`; Codex reads `AGENTS.md` and can use `.codex/config.toml`. See [harnesses](harnesses.md) for the limitations and Hermes.

Optional Git hooks:

```bash
python3 scripts/openass.py hooks install
python3 scripts/openass.py hooks status
```

Create a GitHub issue with acceptance criteria. Open a PR with these lines:

```text
Issue: #123
Risk: standard
Verification: commands and results
```

Critical PRs additionally need `Security review:` evidence and authorized approval. Set required `template-contracts`, `pr-risk` and application checks plus an independent reviewer via **GitHub Settings → Rulesets**.

After CI and review, verify the actual GitHub evidence:

```bash
python3 scripts/openass.py attest --repo OWNER/REPO --pr 123
```

See [operations](operating-system.md), [skills](skills.md), and [architecture](architecture.md).
