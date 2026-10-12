# Open Agent Engineering

**A GitHub-native, agent-independent way to specify, build, verify, and ship software.**

This is a public alpha GitHub project-template foundation. It is not a new coding agent or another mandatory orchestrator.

## Principles

- Git owns accepted specs, implementation, code and decisions. GitHub Issues own work requests; PRs own proposed changes.
- An executor may be Hermes, Codex, Claude Code, Gemini, OpenBot, or a future agent. All use the same task and evidence contracts.
- Spec Kit is the primary optional spec-development workflow. Selected Superpowers skills improve implementation, not duplicate planning.
- Scripts and independent GitHub checks provide evidence. Agents cannot approve their own implementation.
- Use risk-appropriate fast, standard, and critical paths.
- No Cloudflare, Paperclip, memory database, paid model, or hosted service required for the core.

## Start

1. Read PROJECT.md, ARCHITECTURE.md, POLICY.md and AGENTS.md.
2. Install requirements-dev.txt and run python3 scripts/verify.py to verify **this template only**.
3. Copy the template, replace the project placeholders, then initialize with python3 scripts/init_project.py --name sample --app-check python3 -m pytest -q (adjust for your stack).
4. Open an issue with acceptance criteria and an appropriate risk tier. Work on a branch and submit a PR.
5. Turn on required GitHub checks and default-branch protection in repository settings. A template cannot enable those policies itself.

## Directory map

- sops/: risk-adaptive lifecycle, from research to release
- contracts/: portable JSON schemas for agent execution and evidence
- .agents/skills/: small reusable and reviewable skills
- scripts/: deterministic verification, initialization and diagnostics
- tests/: contract and rejection-path tests
- docs/: architecture, component selection, interoperability, benchmarks, and skill security
- .github/: issue, PR and CI conventions

## What is not claimed

Template self-tests are not application verification, production security certification, or benchmarks demonstrating productivity gains. Agent evidence is a claim until checked against the actual commit and CI result.

This repository replaces a January-era methodology while retaining its history. It is a new design and deliberately does not inherit the old protocol as an architecture. The repository can be renamed and enabled as a template through GitHub Settings.

Licensed under MIT. Third-party tools remain optional and carry their own licenses.

## Interpretable Context Methodology (ICM)

Context selection is a **core** part of this template, based on Jake Van Clief and David McDermott's [Interpretable Context Methodology](https://github.com/RinDig/Interpretable-Context-Methodology). Start at `AGENTS.md`, read the root `CONTEXT.md` router, load a stage contract, then only the reference files and working artifacts needed for the task. No extra agent runtime is required.

`python3 scripts/context.py check` verifies routing and stage contracts. `python3 scripts/context.py plan implement --working examples/task.json` prints the precise selected files and their hashes without dumping all context into a prompt. See [docs/context-methodology.md](docs/context-methodology.md).
