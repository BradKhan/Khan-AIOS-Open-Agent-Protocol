# GitHub administration and live harness compatibility

Open ASS cannot alter repository administration through the currently connected GitHub app. The repository includes a dry-run-first, authenticated **owner command** for the remaining controls.

```bash
python3 scripts/openass.py github-admin --repo BradKhan/open-ASS
```

This previews template mode, merged topics, and an active branch ruleset requiring GitHub Actions checks by their verified app ID (15368), with independent human review, last-push review, no force push/deletion, and no bypass actors. It makes **no changes**.

Once a distinct authorized collaborator is available to approve work, the owner can sign in locally with `gh auth login` (with repository administration permissions) and explicitly apply:

```bash
python3 scripts/openass.py github-admin --repo BradKhan/open-ASS --apply --confirm BradKhan/open-ASS --reviewer-ready
```

**Do not paste GitHub tokens into chat or commit them.** `GITHUB_TOKEN`, `GH_TOKEN`, or an authenticated `gh` CLI supplies credentials locally. This command can block future merges if the required collaborator is absent, so `--reviewer-ready` is mandatory. It also checks for a distinct write-access collaborator before making any settings changes. `--require-codeowners` is optional and should only be enabled after `.github/CODEOWNERS` includes a distinct eligible reviewing collaborator. It does not auto-invite collaborators or assign reviewers.

CI checks to require are: `template-contracts`, `pr-risk`, `sdk-compatibility (3.11)`, `sdk-compatibility (3.13)`, `actions-security`, `browser-fixtures`, and `harness-cli`. The browser workflow now runs on every PR so a required status never disappears on docs-only changes.

The separate `harness-cli-compatibility` workflow installs pinned upstream **Codex 0.162.1** and **Claude Code 2.1.296** in an ephemeral credential-free runner. Claude's npm package requires a post-install step to place its native binary; CI deliberately permits that install script in this unprivileged, isolated job and validates their **real help and version output**. It never sends prompts or authenticates inference. Hermes's CLI flags were cross-checked against the upstream Hermes v0.21.x parser and docs; users with a local Hermes installation can validate it by running:

```bash
python3 scripts/openass.py harness-check --harness hermes --strict
```

Full authenticated task execution needs your provider credentials and host sandbox. A working local CLI is not proof of billing limits or semantic correctness.

Social preview artwork still needs to be uploaded manually in GitHub Settings, because GitHub does not expose that feature through the supported repository API.

Claude Code's `--max-turns` is documented but intentionally absent from the CLI `--help` output (Anthropic issue #16963). The executable contract check therefore validates visible flags and separately tests that the adapter retains the documented hidden turn limiter. No prompt is sent to authenticate this behavior in CI.
