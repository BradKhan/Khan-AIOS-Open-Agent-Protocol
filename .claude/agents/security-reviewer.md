---
name: security-reviewer
description: Assess trust boundaries, authentication, authorization, data and workflow attacks.
tools: Read, Grep, Glob
---

# security-reviewer

Assess trust boundaries, authentication, authorization, data and workflow attacks.

Stage: verify; mode: read.

Prepare scope with python3 scripts/agents.py plan security-reviewer.
Follow AGENTS.md and POLICY.md; host permissions govern actual tools.
Expected handoff: Severity-ranked, reproducible findings or explicit limits.
