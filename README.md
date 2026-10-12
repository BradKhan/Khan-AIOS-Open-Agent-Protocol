# Open Agent Engineering

**Keep the engineering. Change the agent.**

A GitHub-native starting point for building software with AI agents. Your repository holds the requirements, context, working rules, and checks. You can change models, hand work to another agent, or bring in a human developer without rebuilding the process from a chat history.

[Get started](#get-started) · [How it works](#how-work-gets-done) · [What's included](#whats-in-the-repository) · [Contribute](CONTRIBUTING.md)

![Verification workflow](https://github.com/BradKhan/Khan-AIOS-Open-Agent-Protocol/actions/workflows/verify.yml/badge.svg)

## Why I built this

I use different models and coding agents for different jobs. A research conversation becomes an issue. One agent implements the feature; another reviews it. Then something changes, and the next agent has to reconstruct the reasoning from scattered messages.

I've also seen an agent declare a task finished when the tests weren't run, the design wasn't right, or the original requirement had quietly changed.

A repository should be able to answer a few basic questions:

- What are we building, and why?
- Which decisions are settled?
- What does this agent need to know for this task?
- What can it change without asking?
- What actually passed, at which commit?

Open Agent Engineering puts those answers in files and GitHub workflows that people can read and agents can use.

## What changes in practice

**Work has a clear starting point.** GitHub Issues carry acceptance criteria. Substantial changes have an approved specification and plan. The agent works from the same versioned requirements a reviewer sees.

**Context is deliberate.** The [Interpretable Context Methodology](docs/context-methodology.md) gives agents a route through the repository: orientation, the current work stage, canonical references, and task-specific files. The `context.py` tool can list selected files and hashes, so a handoff is inspectable instead of an enormous pasted prompt.

**The process fits the risk.** A copy fix, a new product feature, and a permissions change shouldn't go through identical procedures. The [fast](sops/fast.md), [standard](sops/standard.md), and [critical](sops/critical.md) paths specify what each requires.

**Checks are executable.** Task and evidence contracts have JSON schemas. The verifier runs actual configured commands and rejects missing application checks after initialization. GitHub Actions runs independently of the coding agent.

**Approval stays accountable.** Agents work on branches and propose changes. Review and merge decisions remain with the authorized people and checks. A generated evidence file is a claim until someone verifies the corresponding run and commit.

## How work gets done

```text
GitHub issue + acceptance criteria
    ↓
Relevant context + plan
    ↓
Agent or developer works on a branch
    ↓
Tests + independent checks
    ↓
Pull request + review
    ↓
Approved change
```

The stages stay consistent, but the amount of planning and review depends on the work. A routine fix can move quickly. Changes involving authorization, money, sensitive data, or production infrastructure require stronger checks and explicit approval.

There's no prescribed coding model or mandatory orchestrator. Use your preferred agent, IDE, terminal, or team. Paperclip, Hermes, Codex, Claude Code, and other runtimes can fit this model, but their end-to-end integrations still need to be tested and developed.

## Get started

Copy this repository into a new GitHub project. The repository owner can also enable GitHub's **Template repository** setting to expose the usual **Use this template** button.

Install the development dependencies and check the starting structure:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/verify.py
```

At first, the verifier reports **TEMPLATE SELF-TEST ONLY**. That's intentional. The framework hasn't tested your application yet.

Fill in [PROJECT.md](PROJECT.md) and [ARCHITECTURE.md](ARCHITECTURE.md), configure a real application check, then initialize your project. For example, in an application with an existing `npm test` command:

```bash
python3 scripts/init_project.py --name my-app --app-check npm test
python3 scripts/verify.py
```

Replace `npm test` with the verification command your project actually uses. Add the required security command for critical projects.

To inspect the context selected for a task:

```bash
python3 scripts/context.py check
python3 scripts/context.py plan implement --working examples/task.json
```

Read the [quickstart](docs/quickstart.md) for the full first-PR workflow.

## What's in the repository

| Where | What it's for |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) and [`POLICY.md`](POLICY.md) | Rules, boundaries, and who can approve what |
| [`CONTEXT.md`](CONTEXT.md) and [`context/`](context/) | Interpretable, stage-specific context routing |
| [`sops/`](sops/) | Practical procedures for research, development, review, and release |
| [`contracts/`](contracts/) | Portable task and evidence schemas |
| [`.agents/skills/`](.agents/skills/) | Reviewed examples of reusable agent skills |
| [`scripts/`](scripts/) and [`tests/`](tests/) | Deterministic checks and rejection-path tests |
| [`.github/`](.github/) | Issue templates, PR expectations, and CI |
| [`docs/`](docs/) | Architecture, integration rules, tooling research, and benchmarks |

## Built to work with the tools you choose

We borrow useful methods instead of creating a second implementation of every tool:

- [GitHub Spec Kit](https://github.com/github/spec-kit) for more substantial specification and planning work.
- [Superpowers](https://github.com/obra/superpowers) for practices such as test-driven development, debugging, and worktree isolation.
- [Agent Skills](https://agentskills.io/specification) for portable `SKILL.md` conventions.
- [Interpretable Context Methodology](https://github.com/RinDig/Interpretable-Context-Methodology) for clear context routing and handoffs.
- GitHub Actions and your own test commands to check the work.

These are references and optional integrations, not dependencies silently installed by the template. The [component review](docs/selection.md) explains the choices and alternatives.

## Status and contributions

**Alpha.** The repository includes working contract validation, context routing, test fixtures, and GitHub CI. It does not yet demonstrate better performance across coding agents, and its own checks do not certify a new application's correctness or security. Real-world examples, harness compatibility testing, and comparative benchmarks are still work to do.

This is meant to be used, challenged, and improved in public. If a rule gets in the way without preventing a real failure, let's revisit it. If a skill makes an agent measurably better, bring the evidence.

Open an [issue](https://github.com/BradKhan/Khan-AIOS-Open-Agent-Protocol/issues) or read [CONTRIBUTING.md](CONTRIBUTING.md) to get involved.

Created by [Brad Khan](https://github.com/BradKhan). [MIT licensed](LICENSE).
