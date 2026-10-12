# Skills and profiles

Open ASS ships with two native skills: [task-contract](../.agents/skills/task-contract/SKILL.md) and [verification-review](../.agents/skills/verification-review/SKILL.md). External skill packages are **opt-in**, version-pinned, and installed as instruction files plus text references. The template never executes downloaded scripts.

## Curated profiles

| Profile | Selected capabilities |
| --- | --- |
| `core` | Superpowers debugging, TDD, worktrees and verification; Sentry bug-finding and PR iteration |
| `web` | Taste, Impeccable, Vercel Web Interface Guidelines and React best practices, Anthropic frontend design, Playwright CLI skill |
| `security` | Sentry security, GitHub Actions security, and skill-scanner |
| `writing` | Humanizer |
| `authoring` | Anthropic Skill Creator |

**Core installation is optional:** Open ASS's GitHub contracts, SOPs, ICM routing, and verification work without installing any third-party skill. The catalog identifies available skill instruction packages; installing one does not install its executable dependencies, framework plugins, CLIs, or paid services.

## Commands

```bash
python3 scripts/skills.py list
python3 scripts/skills.py plan --profile core --profile web
python3 scripts/skills.py install --profile core --profile web
python3 scripts/skills.py check
python3 scripts/skills.py audit
```

To limit context and downloads, install just one: `python3 scripts/skills.py install --skill impeccable`. Multiple `--profile` and `--skill` flags are supported. No external installer is invoked.

Packages are written under `.agents/skills/<skill-name>/` with a `.open-ass-source.json` provenance manifest recording every installed file's SHA-256. Existing managed or unmanaged directories are never silently overwritten. To change a version, audit and remove the old managed directory yourself, update the pinned catalog after review, and reinstall. `check` verifies the registry and installed snapshots without network access. `plan` also works offline.

The installer fetches the GitHub source tree at an exact commit SHA, downloads only non-executable Markdown and other approved text formats, and verifies each file against its Git blob SHA before writing it. Symlinks, scripts, binaries, and executables are excluded. A failed download should leave the requested skill uninstalled. Downloaded instructions must still be treated as **untrusted content** and reviewed before allowing agents to use them.

## Which skill runs when?

- **Specification or planning:** Use [Spec Kit](https://github.com/github/spec-kit) for substantial features. Don't run Superpowers brainstorming or planning again after accepting a Spec Kit plan.
- **Implementation:** Use Superpowers TDD/debugging/worktrees and `verification-before-completion`, when applicable.
- **UI/UX:** Start with Taste for landing pages or design direction, then Impeccable for bounded critique and polish. Use Vercel guidelines for accessibility/usability and React best practices for React/Next.js code. Run actual browser tests separately.
- **Security:** Use reviewed Sentry skills plus actual static analyzers. A skill's opinion is not a security certificate.
- **Copy and technical writing:** Humanizer is a *revision* skill, not a source of facts.
- **Skill authoring:** Skill Creator helps refine and evaluate skills; executable evaluation helpers from upstream are **not** installed by the text-only installer.

Skills are selected per task via [ICM](context-methodology.md), not concatenated into every model context. This avoids conflicting instructions and unnecessary tokens.

## Known limitations

- **Impeccable** includes commands and asset-producing features in its full upstream package. This installer provides only its text instructions and text references; capabilities requiring excluded executables need separately reviewed installation.
- **Vercel Web Interface Guidelines** instruct the agent to fetch a latest-version external document at task time. That content is *not covered* by the pinned skill revision. Treat runtime fetches as untrusted and separately pin or review the guideline content where reproducibility matters.
- **Playwright CLI** still requires its own executable setup and browser installation. An installed SKILL.md cannot substitute for browser automation.
- **Anthropic Skill Creator** similarly references evaluation scripts that are excluded from the instruction-only installation.
- Compatibility with any specific agent harness is **not yet verified end-to-end**. Keep failed installs and runtime incompatibilities visible and submit reproductions as GitHub issues.
- Runtime enforcement of agent permissions, network restrictions, and tool capabilities belongs to the harness/sandbox. Repository prose alone does not enforce isolation.

Catalog details (including upstream links and exact commits) are in [integrations/skills.lock.json](../integrations/skills.lock.json). Licensing varies across projects; consult upstream before redistributing source material.

## Adding a skill

Document the source, exact upstream commit SHA, install path, license, task scope, and why it improves on the existing profile. Audit the instruction bundle for credential requests, policy overrides, hidden fetches, or executable steps. Then add a representative test/evaluation and submit a focused PR. Avoid importing alternative planning frameworks that replicate the same phase.
