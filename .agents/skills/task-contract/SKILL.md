---
name: task-contract
description: Turn a GitHub issue and accepted specification into a portable bounded agent task. Use before delegation to any executor.
---

# Task contract

1. Read the GitHub issue, canonical spec and POLICY.md.
2. Preserve user-visible intent and exact acceptance criteria; do not silently change them.
3. Set fast/standard/critical risk according to the actual impacts.
4. Produce JSON conforming to contracts/task.schema.json.
5. Take budgets, attempt ceilings and base SHA from authorized controls. Do not invent permission or spending authority.
6. Link execution and PR status to the canonical issue.
7. This JSON requests work; it cannot approve a merge, deployment or change CI policy.
