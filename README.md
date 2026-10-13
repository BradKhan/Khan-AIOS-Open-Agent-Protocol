<p align="center">
  <img src="assets/open-ass-donkey.png" alt="A grinning gold pixel-art donkey, looking back over its shoulder" width="210">
</p>

# Open ASS

### Open Agent Software System

**Get your ASS together.**

AI agents can write an entire application in minutes. Getting them to build the *right* thing, make it look good, write like a human, work together, catch their mistakes, and ship something worth using?

**Still a pain in the ass.**

Every new project seems to start the same way. Configure your agents. Install your favorite skills. Write another set of instructions. Explain your architecture for the fifth time. Then spend hours fixing ugly interfaces, rewriting robotic copy, and debugging code that was supposedly finished.

Switch models, lose context, add another agent, and repeat.

I built Open ASS because I got tired of rebuilding the development process every time I wanted to build something.

**It's a ready-made, open-source development system that brings the tools, skills, and practices of good software engineering into one GitHub repository.**

You bring the idea and your preferred AI agents. Open ASS gives them a common way to work, from figuring out what to build through design, implementation, testing, and release.

The aim is simple: spend more time building useful software and less time managing the machinery around it.

## Good software takes more than good code

An application can compile perfectly and still be terrible.

The requirements were misunderstood. The interface looks like every other AI-generated dashboard. The copy reads like a cyborg having an identity crisis. Something important breaks the moment a user does anything unexpected.

Open ASS addresses the whole development process.

### Engineering

Clear requirements, sensible architecture, structured development, systematic debugging, testing, and code review.

The framework draws on GitHub Spec Kit, Superpowers, Sentry, and established engineering practices. Small changes can move quickly. Riskier work gets more scrutiny.

There's a process for getting things done, without making every bug fix feel like a government procurement exercise.

### Design

Nobody wants another dashboard full of purple gradients, meaningless cards, and buttons that look pretty but don't do anything useful.

Open ASS brings together Taste, Impeccable, Vercel's Web Interface Guidelines, React best practices, and frontend design skills.

These give agents better guidance for visual identity, usability, accessibility, performance, and the details that separate a working interface from a damn good one.

### Writing

Your landing page shouldn't sound like a press release written by a committee of chatbots.

Humanizer and writing practices help cut the buzzword soup, fake enthusiasm, corporate filler, and the relentlessly predictable phrasing that makes AI-generated copy so easy to spot.

That applies to marketing pages, documentation, onboarding, interface text, and everything else users actually read.

### Context and coordination

An agent shouldn't need your entire chat history explained every time it picks up a task.

Open ASS uses Interpretable Context Methodology (ICM) to organize project knowledge, route agents to relevant instructions, and make handoffs inspectable.

Requirements, decisions, and accepted changes live in GitHub. You can change models or involve another developer without losing the project's direction.

### Testing and verification

An agent saying "Done!" doesn't mean the work is done.

Open ASS includes task contracts, automated checks, security review procedures, and GitHub CI. Changes can be evaluated against the original requirements and actual test results.

Agents can propose work and report what happened. Independent checks and authorized reviewers determine whether it's ready.

## What's already in the ASS?

The repository currently includes:

- A GitHub-native development framework with specifications, policies, and risk-based workflows.
- Five curated skill profiles covering engineering, web/design, security, writing, and skill creation.
- 17 pinned external skills with an installer that verifies downloaded files and records their provenance.
- ICM context routing to organize instructions and task handoffs.
- Verification scripts, automated tests, and CI workflows.
- A foundation for adding specialist agents, orchestration, and persistent memory as projects grow.

You don't need to install everything. Pick the capabilities relevant to your project.

The core works with GitHub and Python, without requiring a paid AI service or dedicated orchestration platform. Some external skills need additional tools to unlock their full functionality.

And your workflow stays in your repository, where it won't disappear when the next model comes along.

### Operational tools

Open ASS now includes a single [CLI](docs/operating-system.md), [specialist agent handoffs](config/agents.json), opt-in Git hooks and a **read-only local MCP server** for scoped context and skill metadata. See the [harness guide](docs/harnesses.md) for Claude Code, Codex and Hermes support.

```bash
python3 scripts/openass.py doctor
python3 scripts/openass.py agents plan engineer
python3 scripts/openass.py hooks install
python3 scripts/openass.py verify
```

PRs are checked for declared risk and sensitive changes. After independent review, `openass.py attest` can query actual GitHub checks and current-head approvals. This cannot replace GitHub branch rulesets, application testing or authorized reviewers.

## Get your ASS up and running

Copy Open ASS into a repository you control. Python 3.11+ and Git are sufficient for the core.

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/openass.py doctor
python3 scripts/openass.py verify
```

The initial run verifies the framework, **not your application**. Initialize a copied project with its actual test command and GitHub owner:

```bash
python3 scripts/openass.py bootstrap --name my-app --owner YOUR_GITHUB_LOGIN --app-check npm test
python3 scripts/openass.py bootstrap --name my-app --owner YOUR_GITHUB_LOGIN --apply --app-check npm test
```

The first command is a dry run. The second configures the project and replaces upstream CODEOWNERS; it never runs your supplied test command. Complete PROJECT.md and ARCHITECTURE.md and verify the app.

Add curated capabilities as needed:

```bash
python3 scripts/openass.py skills list
python3 scripts/openass.py skills install --profile core --profile web
python3 scripts/openass.py role-sync check
python3 scripts/openass.py harness --harness hermes --role engineer
python3 scripts/openass.py quality plan
python3 scripts/openass.py evaluate
```

The task runner now supervises actual CLI processes, records heartbeats, permits cancellation/recovery, and verifies usage where the provider reports it. It refuses dirty checkouts and never treats a model's exit code as GitHub approval.

For an already-approved task with a budget:

```bash
python3 scripts/openass.py run run TASK-ID --harness codex --role engineer --actor worker --reserve-cents 100
```

That's a preview. To authorize a real run, append `--execute --ack-unmetered`; see [supervision and cost boundaries](docs/supervisor.md). You can also check a runtime with a disposable coding fixture:

```bash
python3 scripts/openass.py live-smoke --harness claude
```

Open ASS v0.5 also adds an offline container execution boundary, commit-bound PR verification, and risk-adaptive role/skill selection. Preview the selected capabilities or run the reproducible evaluation fixtures:

```bash
python3 scripts/openass.py activate --description "Redesign the responsive UI" --path app/page.tsx
python3 scripts/openass.py bench plan
python3 scripts/openass.py bench self-test
```

The evaluation runner has 18 tasks and 56 acceptance cases. It does **not** claim proven model performance improvements: authenticated model comparisons, measured cost data, and independent real-world benchmarks still need to be run. See [evaluation suite](docs/benchmarks.md) and [commit-bound dispatch](docs/dispatch.md).

The smoke command is also dry-run-first. Real, authenticated runs need your own CLI account; see [live agent testing](docs/live-smoke.md). To inspect and enable the GitHub owner settings, see [repository administration](docs/github-administration.md). The connected GitHub integration cannot turn those settings on from this chat.

Harness commands are **dry-run-first**, and third-party tools may need their own installation. A local task lifecycle, read-only MCP server, browser evidence gate and GitHub attestation tool are included. Neither code generation nor a green template test substitutes for verified application behavior or authorized review.

[Quickstart](docs/quickstart.md) · [Skills](docs/skills.md) · [Agent harnesses](docs/harness-runtime.md) · [Task lifecycle](docs/lifecycle.md) · [Product quality](docs/product-quality.md) · [Release evaluations](docs/release-evaluation.md)

## Built in the open

Open ASS is free, MIT licensed, and under active development.

The framework, skill installer, context routing, and verification system are working. The supervised runtime, sandbox option, and repeatable evaluation harness are implemented, but authenticated end-to-end comparisons, broader automation, and published performance results are still being developed.

There's plenty to improve. If you find a better engineering practice, a useful skill, or a problem the framework fails to catch, bring it in. Working examples and reproducible tests are especially welcome.

I want this to become the kind of repository you reach for whenever you're starting a software project, because it saves you from setting up and fixing the same things over and over.

**AI can already generate the code. Let's make it better at everything else it takes to ship a damn good product.**

[Contribute](CONTRIBUTING.md) · [Report an issue](https://github.com/BradKhan/open-ASS/issues)

Created by [Brad Khan](https://github.com/BradKhan). MIT licensed.
