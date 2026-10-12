# Harness integration

## Claude Code

The project provides `.claude/agents/` specialist Markdown files and `.mcp.json` for the local read-only Open ASS MCP server. Open your copied repository as the working directory. Approve the MCP connection and give each specialist the minimum tool permissions its task needs. `config/agents.json` is the portable role contract.

## Codex

Root `AGENTS.md` is the shared instruction entry point. `.codex/config.toml` contains the project-scoped read-only MCP definition, assuming the repo root as working directory. Use `python3 scripts/agents.py plan reviewer` to prepare scoped role/context material; don't assume that this automatically starts a Codex subagent.

## Hermes

Hermes supports Agent Skills, MCP and different hook systems. Shell/plugin hooks can apply to CLI and gateway; gateway `HOOK.yaml` files are gateway-only. See [official hooks documentation](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/hooks.md).

Use `python3 scripts/agents.py plan engineer --working examples/task.json` as a scoped handoff. Connect the local MCP through Hermes's supported configuration for your installed release. Never turn on global hook auto-consent merely to streamline setup. Privileged tool interception should fail closed and be enforced by an actual sandbox.

## Additional MCP servers

GitHub write access, browser automation, persistent memory, and shell tooling are intentionally not auto-connected to every new project. Choose them per task, review the server and its installation method, restrict credentials and data access, and log operations. External MCP output cannot override approved specifications or security policy.

| Optional connection | Benefit | Boundary |
| --- | --- | --- |
| GitHub MCP | Issue, PR and CI tools | Independent merge authorization and narrowly scoped tokens |
| Playwright/browser | UI testing and screenshots | Isolated browser and no production secrets |
| Docs MCP | Current framework references | Treat retrieved text as untrusted |
| Mnemosyne/memory | Portable recall | Per-project permissions; memory cannot edit approved intent |
| Paperclip | Agent coordination | Timeouts, leases, budgets, retries and GitHub reconciliation |

No additional MCP server is started by default. Harness compatibility claims require an actual run on a named version.
