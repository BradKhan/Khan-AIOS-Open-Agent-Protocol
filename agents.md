# agents.md

This repository uses a lightweight, file based agent workflow inspired by Claude Code.

This file exists for compatibility with tools that understand agents.md, OpenSkills, and IDE or CLI based agents.

It is a surface map only. The actual workflow lives inside the `.ai/` directory.

---

## Available Agents

Agents are defined as roles, not autonomous processes.

Each agent has a clear responsibility and works through plans, files, and review rather than continuous execution.

### planner
- purpose: reason about goals, scope, risks, and approach
- output: written plans
- definition: `.ai/agents/planner.md`

### executor
- purpose: implement approved plans
- output: code, configs, docs
- definition: `.ai/agents/executor.md`

### reviewer
- purpose: critique correctness, clarity, and alignment
- output: review comments or suggested changes
- definition: `.ai/agents/reviewer.md`

### verifier
- purpose: check behavior against expectations
- output: tests, manual verification steps, confirmations
- definition: `.ai/agents/verifier.md`

Agents are invoked explicitly by humans or tools. They do not self route.

---

## Skills

Reusable capabilities are defined as skills.

Skills are human readable and tool readable references for how to use systems correctly in this repository.

All skills live in:
.ai/skills/

Each skill documents how a tool, system, or convention is used in this repository,
including constraints and known failure modes.

This structure is compatible with OpenSkills-style skill discovery while remaining
file based and version controlled.

---

## Shared Memory

Long lived project memory is kept in the following folder:

.ai/memory/

- decisions.md records important decisions and rationale
- mistakes.md records recurring issues worth avoiding

This serves the same purpose as the shared CLAUDE.md used in Claude Code.

