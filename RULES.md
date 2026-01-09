# RULES

This file defines non negotiable rules for work in this repository.

If there is any conflict between behavior, tools, agents, or models, these rules apply.

---

## Authority Order

1. RULES.md
2. AGENT.md
3. .ai/agents/*
4. .ai/skills/*
5. Tool or model defaults

Lower levels do not override higher ones.

---

## Planning Discipline

- Non trivial work requires an explicit plan.
- Execution without a plan is a violation.
- Plans must state how success will be checked.

---

## Role Separation

- Planner, executor, reviewer, and verifier roles must not be mixed implicitly.
- Role switches must be explicit.
- Skipping review or verification is not allowed unless explicitly justified.

---

## Memory Updates

Update shared memory when:
- the same mistake happens more than once
- an assumption proves false
- a constraint becomes explicit
- a workaround becomes permanent

Memory lives in:
.ai/memory/

---

## Tool Behavior

When unsure:
- stop
- ask a question
- propose a plan

Guessing and silent assumptions are not acceptable.

---

## Scope Control

Do not:
- add files not justified by the plan
- change unrelated code or structure
- vendor external repositories without explicit intent

Keep changes minimal and explain deviations.
