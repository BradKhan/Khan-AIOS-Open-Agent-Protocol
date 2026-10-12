# Harness CLI and MCP profiles

Use python3 scripts/openass.py harness --harness codex|claude|hermes --role ROLE to inspect a safe dry-run command and whether the CLI is installed. Add --execute only after reviewing the command, scope, available credentials and agent sandbox. Executing a real agent may incur cost and modify files for writable roles.

Codex uses codex exec with explicit read-only or workspace-write sandbox; Claude Code uses claude -p with plan-mode for read-only specialists; Hermes uses one-shot chat, query from stdin, structured stream-json events, bounded turns, and worktree/checkpoints for editing roles. Read roles request the restricted `skills` toolset. **Do not use `--safe-mode` for ordinary Open ASS execution**: it disables project instructions, hooks, MCPs and skills. Noninteractive Hermes modes can bypass interactive approvals; constrain terminal permissions in the host sandbox and grant execution consent explicitly. Actual CLI options vary across versions; check the local --help when upgrading. No shell interpolation or automatic merge.

Handoffs carry scoped context text and hash provenance, using the role registry. Scripted runs are bounded by an explicit timeout, and results report the actual process exit code. The runtime's own token/tool budgets, approvals, filesystem isolation and network access are still enforced by the runtime, not this adapter.

Available MCP profiles are documented as opt-in capabilities in config/mcp-profiles.json. External GitHub, Playwright, and memory connectors are **not auto-installed or automatically trusted**. Provide credentials with minimum scopes and do not permit external MCP output to override accepted repository policy.

CLI syntax sources: https://developers.openai.com/codex/non-interactive , https://code.claude.com/docs/en/cli-reference , https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/cli-commands.md
