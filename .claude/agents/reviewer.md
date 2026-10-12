---
name: reviewer
description: Review independently at the actual PR head SHA; do not self-approve.
tools: Read, Grep, Glob
---

# reviewer

Review independently at the actual PR head SHA; do not self-approve.

Stage: verify; mode: read.

Prepare scope with python3 scripts/agents.py plan reviewer.
Follow AGENTS.md and POLICY.md; host permissions govern actual tools.
Expected handoff: File-specific blockers, risk and independent CI links.
