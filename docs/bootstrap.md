# Safe bootstrap and role synchronization

The project must not inherit the upstream author's CODEOWNERS. Run bootstrap with --name and --owner plus a real --app-check. Without --apply it is a dry run; with --apply it writes only config/project.json and .github/CODEOWNERS. It does not run test commands or configure GitHub rulesets. Owner-specific approvals must be configured in GitHub settings.

The nine Claude Code specialist files are generated from config/agents.json. Run python3 scripts/openass.py role-sync write after editing the registry; CI runs role-sync check to reject drift. These are role descriptions, not permission enforcement or automatically spawned agents. Codex and Hermes still use the portable registry and their native runtime configurations.
