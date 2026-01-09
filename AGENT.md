# AGENT.md

This file defines how work is done in this repository by humans and AI tools.

Its purpose is to reduce ambiguity, reduce errors, make collaboration easier, and allow learning to compound over time.

This file is the canonical behavioral and memory contract for the project.
If there is a conflict between tools, skills, agents, or model behavior, this file takes precedence.

---

## Project Orientation

Project name:
[PROJECT NAME]

What this is:
[ONE OR TWO SENTENCES DESCRIBING THE PROJECT IN PLAIN LANGUAGE]

What success looks like:
[THE PRIMARY OUTCOME THIS PROJECT IS TRYING TO ACHIEVE]

What this is not:
[IMPORTANT NON GOALS OR THINGS INTENTIONALLY OUT OF SCOPE]

---

## Why This Workflow Exists

This project uses an agent oriented workflow inspired by the practices developed by the creator of Claude Code.

The core idea is that most gains come from clarity around how work is planned, executed, reviewed, and verified, not from any single model or tool.

Claude Code expresses this through shared memory (CLAUDE.md), explicit planning, reusable commands, subagents, Skills, and tool integrations.

Here, the same ideas are implemented using plain files and conventions so the workflow remains model agnostic, tool agnostic, and easy to reason about.

---

## Shared Memory and Authority

This file plays the same role as CLAUDE.md in Claude Code.

It is the highest authority for:
- behavioral expectations
- workflow discipline
- project specific constraints
- accumulated lessons

Skills, tools, agents, and models may assist with execution, but they do not override the rules or intent captured here.

When something goes wrong repeatedly, the fix belongs here.

---

## How Work Is Done

### Planning first

Non trivial work begins with a plan.

A good plan:
- explains intent and scope
- calls out assumptions and unknowns
- highlights risks or tradeoffs
- explains how the result will be checked

Plans are written and refined before execution.
Execution without a clear plan is discouraged.

Planning discipline is defined in planner.md.

---

### Distinct roles

Different kinds of thinking are separated into explicit roles.

Roles are defined in:
.ai/agents/

Common roles include:
- planner, focused on reasoning and options
- executor, focused on implementation
- reviewer, focused on critique
- verifier, focused on checking behavior

Agents should switch roles explicitly rather than mixing concerns.
This mirrors the planner and executor separation used in Claude Code.

---

### Closing the loop

Work is only complete when there is a way to check that it worked.

Verification can include:
- tests
- scripts
- manual checks with clear steps

If verification is missing, the work is incomplete.
Verification expectations are defined in verifier.md.

---

## Tools, Skills, and External Systems

### Skills

This project supports two categories of skills.

Project specific skills live in:
.ai/skills/

These document how tools and workflows are used in this project, including limitations and common failure modes.

Standardized, reusable skills may also be installed using the OpenSkills format.
These live in:
skills/

Standardized skills follow the SKILL.md convention and are declared in agents.md.

All skills are helpers.
They do not override this file.

If a skill causes repeated mistakes or confusion, the correction belongs here.

---

### agents.md

This project includes an agents.md file to support emerging open standards for agent and skill declaration.

agents.md exists for interoperability and discovery only.

Behavioral authority, planning discipline, and shared memory live in this file.
If there is any disagreement, this file takes precedence.

---

### External systems

This project may interact with external systems such as source control, CI, databases, or messaging tools.

Access is usually provided through existing integrations such as VS Code extensions or command line tools.

Conceptually, this serves the same role as Claude Code’s tool integrations, without depending on a specific protocol.

If an external system becomes important or non obvious, it should be documented as a skill.

---

## Constraints and Boundaries

Some constraints are worth making explicit:

- [ARCHITECTURAL CONSTRAINT]
- [LANGUAGE OR FRAMEWORK PREFERENCE]
- [SECURITY, PERFORMANCE, OR RELIABILITY CONSIDERATIONS]

If a constraint needs to change, it should be discussed openly rather than worked around implicitly.

---

## Learning Over Time

This project improves through shared, versioned memory.

When a human or AI:
- makes a repeated mistake
- misunderstands an instruction
- violates an implicit assumption
- requires repeated correction

that insight should be captured.

Supporting memory files include:
.ai/memory/mistakes.md
.ai/memory/decisions.md

Updating these files during iteration or review is encouraged.

This serves the same purpose as the shared memory practices used with CLAUDE.md in Claude Code.

---

## How to Use This File

For humans:
- read this when joining the project
- update it when goals, constraints, or lessons change

For AI tools:
- treat this as shared context
- ask clarifying questions when unsure
- follow planning and execution discipline
- optimize for correctness and understanding

---

## When Unsure

When something is unclear:
- slow down
- ask questions
- suggest a plan rather than acting immediately

Clarity tends to pay for itself.
