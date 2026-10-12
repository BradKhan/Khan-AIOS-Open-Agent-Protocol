<p align="center">
  <img src="assets/open-ass-donkey.png" alt="A grinning gold pixel-art donkey, looking back over its shoulder" width="210">
</p>

<h1 align="center">Open ASS</h1>
<p align="center"><strong>Open Agent Software System</strong></p>
<p align="center"><strong>Get your ASS together.</strong></p>

<p align="center">
  <a href="docs/quickstart.md">Get started</a> ·
  <a href="docs/architecture.md">How it works</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

AI agents can write code remarkably fast. Getting them to build the *right* thing, work together, remember decisions, catch mistakes, and ship finished software? Still a pain in the ass.

**Open ASS is an open-source engineering system that gets your AI development workflow organized out of the box.**

It brings together proven engineering practices, specifications, agent skills, structured context, automation, and verification in a ready-made GitHub project.

Use your preferred models and coding agents. Start with one. Add more when you need them. Your project, workflow, and engineering standards stay yours.

## Why Open ASS?

The tools are getting better almost daily. The surrounding engineering process hasn't caught up.

You can generate an entire application in minutes, then spend hours fixing misunderstood requirements, reconstructing lost context, debugging unexpected behavior, or figuring out whether the agent actually tested anything.

Every new project starts with another round of configuring tools, writing instructions, and assembling a development workflow.

Open ASS is designed to eliminate that repeated work.

**Less setup. Less babysitting. Better software.**

## What's included

- **A development system, ready to use.** Procedures for defining, building, testing, reviewing, and releasing software.
- **Your agents, your choice.** Portable instructions and task contracts that don't depend on one model or coding platform.
- **Context that makes sense.** [Interpretable Context Methodology](docs/context-methodology.md) (ICM) helps agents find relevant project knowledge and make handoffs inspectable.
- **Better engineering habits.** Specifications, test-driven development, reusable skills, and systematic debugging.
- **Actual verification.** Executable checks, structured evidence, and GitHub CI. An agent saying "done" is not a test result.
- **Room to grow.** Keep things lightweight for small projects. Add specialized agents, orchestration, and persistent memory when they're useful.

## How it works

```text
Define → Plan → Build → Verify → Ship
```

Start with a GitHub issue. Give an agent the relevant context and a clear definition of success. Let it work, test its changes, and submit a pull request.

The framework gives each stage a consistent process and makes the work inspectable.

A minor bug fix doesn't need a small mountain of paperwork. Security-sensitive changes deserve considerably more scrutiny. Open ASS [adapts the process to the risk](POLICY.md).

GitHub remains the shared source of truth. Humans stay in control of consequential decisions.

## The best tools, working together

Open ASS draws on useful work already happening across the open-source engineering community:

- [GitHub Spec Kit](https://github.com/github/spec-kit) for structured specifications and planning.
- [Superpowers](https://github.com/obra/superpowers) for engineering practices and development skills.
- [Interpretable Context Methodology](https://github.com/RinDig/Interpretable-Context-Methodology) for context routing and handoffs.
- [Agent Skills](https://agentskills.io/specification) for portable, reusable capabilities.
- GitHub Actions and deterministic testing tools for independent verification.

We use complementary approaches without making you install every framework under the sun. The [component review](docs/selection.md) explains the decisions.

The core works with repository files, Python, and GitHub. Additional integrations are optional. Support across individual agent harnesses is still being tested.

## Install curated agent skills

The template works without external skills. When you want more capability, choose a [curated profile](docs/skills.md) and install its **pinned, instruction-only** skill packages:

```bash
python3 scripts/skills.py list
python3 scripts/skills.py plan --profile core --profile web
python3 scripts/skills.py install --profile core --profile web
python3 scripts/skills.py check
```

The web profile includes **Taste, Impeccable, Vercel Web Interface Guidelines, React best practices, Anthropic Frontend Design, and the Playwright CLI skill**. Core covers debugging, TDD, worktrees, review, and verification. Security, writing, and skill-authoring profiles are also available.

No remote executable code runs during installation. The full tools and runtime integrations may require separate setup, and installing skills alone does not establish tested compatibility with Hermes, Codex, or another harness. See [how installation and provenance work](docs/skills.md).

## Get started

Copy this repository into a GitHub project. If the repository owner has enabled **Template repository**, click **Use this template** to begin.

Install the development requirements and check the starting structure:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/verify.py
```

At this point, verification checks the *template*, not your application.

Fill in [PROJECT.md](PROJECT.md) and [ARCHITECTURE.md](ARCHITECTURE.md), configure your application's real checks, and initialize. For example, if `npm test` already works in your project:

```bash
python3 scripts/init_project.py --name my-app --app-check npm test
python3 scripts/verify.py
```

Replace `npm test` with the actual test command for your stack. Critical projects require a security check as well.

To inspect which repository files are selected for an implementation-stage handoff:

```bash
python3 scripts/context.py check
python3 scripts/context.py plan implement --working examples/task.json
```

Read the [quickstart](docs/quickstart.md) or explore the [architecture](docs/architecture.md).

## What's in the box?

| Location | Purpose |
| --- | --- |
| [`AGENTS.md`](AGENTS.md), [`POLICY.md`](POLICY.md) | Agent rules, risk levels, permissions, and approval boundaries |
| [`CONTEXT.md`](CONTEXT.md), [`context/`](context/) | Context routing, stage contracts, and reference selection |
| [`sops/`](sops/) | Development procedures from research through release |
| [`contracts/`](contracts/) | Machine-readable task and evidence formats |
| [`.agents/skills/`](.agents/skills/) | Reusable agent skill examples |
| [`scripts/`](scripts/), [`tests/`](tests/) | Deterministic checks and rejection-path tests |
| [`.github/`](.github/) | GitHub issue templates, pull requests, and CI |

## Open source. Open to improvement.

**Open ASS is in alpha.** The core development contracts, context routing, verification scripts, and GitHub workflows are implemented. Broader agent integrations and performance benchmarks are still being developed.

Contributions are welcome, especially working integrations, engineering improvements, reproducible tests, and evidence that a method performs better.

If something is unnecessarily complicated, [open an issue](../../issues). If an agent confidently produces garbage, we'd like a reproducible example.

**Good software takes more than good autocomplete.**

Created by [Brad Khan](https://github.com/BradKhan). [MIT licensed](LICENSE).

[Contribute](CONTRIBUTING.md) · [Report an issue](../../issues) · [Explore the docs](docs/architecture.md)
