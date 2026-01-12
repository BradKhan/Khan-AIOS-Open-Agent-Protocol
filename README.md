# KhanOS Sovereign Development AI Framework

**KhanOS Sovereign AI Development Framework is a sovereign, vendor-agnostic AI engineering framework.**

It is based on the internal workflow discipline pioneered by the Anthropic team
and popularized through Claude Code,
but implemented entirely using plain files, folders, and conventions.

No lock-in.
No proprietary pricing.
No required model or provider.

Use Claude, Gemini, Qwen, OpenAI, local models, or future tools not yet invented.

KhanOS is designed to outlive them all.
﻿## Why This Workflow Exists

This project's workflow is modeled on the engineering practices developed by Boris Cherny, creator of Claude Code.

Claude Code demonstrated that the biggest productivity gains do not come from a single model or tool, but from disciplined structure around how agents think, plan, act, and verify work.

Key ideas adopted here:

- Explicit planning before execution
- Clear separation of roles rather than blended prompting
- Shared, versioned memory of mistakes and constraints
- Reusable workflows instead of repeated ad hoc instructions
- Mandatory verification loops to close the feedback cycle

Claude Code implements these ideas through proprietary features such as CLAUDE.md, slash commands, subagents, permissions, and MCP integrations.

This repository reimplements the same principles using plain files, folders, and conventions so they remain:

- Model agnostic
- Tool agnostic
- Auditable in git
- Shareable across teams
- Durable over time

Nothing in this workflow depends on a specific AI provider. Any capable model, whether accessed via VS Code, CLI, or web UI, can participate as long as it follows the structure.

## Tools, Skills, and External Systems

This repository treats tools and external systems as explicit capabilities rather than implicit magic.

Reusable tool knowledge lives in:
.ai/skills/

Each skill describes:
- what a tool is for
- how it should be used
- constraints and failure modes

External systems such as version control, CI, databases, or messaging platforms are accessed through existing integrations (VS Code extensions, CLIs, APIs).

This serves the same role as Claude Code’s MCP, but without binding the project to a specific protocol or provider.

If a new tool or system is introduced, a corresponding skill should be documented.trae --

---

## How This Maps to Claude Code

Claude Code concept            This repository

CLAUDE.md                      AGENT.md and RULES.md  
Slash commands                 .ai/commands/  
Subagents                      .ai/agents/  
Claude Skills                  .ai/skills/  
Compounding memory             .ai/memory/  
Permission discipline          .ai/settings/  
Plan mode before execution     planner.md role  
Verification hooks             verifier.md role  

The difference is that here the structure is explicit, visible, and editable by humans.

---

## How to Use This as a Default Boilerplate

This repository is intended to be copied as the starting point for new projects.

When starting a new project:
1. Update the first paragraph of this README
2. Rewrite AGENT.md to describe the project and constraints
3. Adjust planner.md and executor.md only if needed
4. Begin recording mistakes and decisions in .ai/memory/

---

## External Standards and Tooling

This boilerplate interoperates with external agent standards and tooling.
They are intentionally not vendored into each project repository.

Upstream references:

- agents.md  
  https://github.com/BradKhan/agents.md  
  Open agent and skill declaration standard used for interoperability.

- OpenSkills  
  https://github.com/BradKhan/open-skills  
  Standardized, reusable skill definitions.

- Gemini CLI  
  https://github.com/BradKhan/gemini-cli  
  Optional CLI interface for interacting with Gemini models.

- Qwen Code  
  https://github.com/BradKhan/qwen-code  
  Optional coding focused model and workflow tooling.

- Trae Agent  
  https://github.com/BradKhan/trae-agent  
  Experimental agent execution and orchestration tooling.

Each project may:
- reference these repositories directly
- fork them if modifications are required
- integrate selectively via `.ai/skills/` and agents.md compatibility

No external repository is required for basic operation of this workflow.

---

## Repository Structure

- AGENT.md  
  Canonical project context, constraints, and shared memory contract.

- RULES.md  
  Hard rules and enforcement boundaries.

- agents.md  
  Interoperability map for tools that understand agent and skill standards.

- .ai/agents/  
  Role definitions such as planner, executor, reviewer, verifier.

- .ai/skills/  
  Project specific and referenced skill documentation.

- .ai/memory/  
  Accumulated decisions, mistakes, and lessons.

---

## Guardrails

This boilerplate is intentionally minimal.

Do not:
- vendor upstream standards or tooling by default
- duplicate skills across projects unnecessarily
- bypass planning or verification discipline

If structure feels heavy, simplify consciously rather than ignoring it.

---

## How KhanOS Compares

**Versus Claude Code**
- Same planning and verification discipline
- No proprietary tooling
- No vendor pricing dependency
- Fully auditable in git

**Versus BMAD**
- BMAD emphasizes roles and cadence
- KhanOS emphasizes authority, intent, and verification
- KhanOS avoids ceremony while preserving rigor

**Versus Spec Kit**
- Spec Kit focuses on artifacts
- KhanOS focuses on workflow invariants and behavioral contracts
- Specs emerge from intent, not the other way around

KhanOS subsumes these approaches by enforcing the underlying assumptions they rely on.
