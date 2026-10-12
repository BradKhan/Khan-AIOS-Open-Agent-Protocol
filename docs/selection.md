# Upstream selection, 12 October 2026

Decision factors: engineering usefulness, portability, maintained upstream, license, attack surface, added cost, and overlap.

| Capability | Preferred reference | Decision |
|---|---|---|
| Specs and planning | github/spec-kit | Primary optional planning workflow, standard/critical paths |
| Debugging, tests, worktrees | obra/superpowers | Selective skills; do not duplicate Spec Kit planning |
| Skill interoperability | agentskills/agentskills | Standard SKILL.md layout |
| Skill creation and evaluation | anthropics/skills | Optional authoring process with regression fixtures |
| Engineering review | getsentry/skills | Select find-bugs and iterate-pr after audit |
| UX/design | pbakaus/impeccable | Optional for product-interface work |
| Web guidelines | vercel-labs/agent-skills | Optional for React and web |
| Browser validation | microsoft/playwright | Deterministic E2E tests |
| Agent evaluations | promptfoo/promptfoo | Optional behavior regression and model comparison |
| Actions security | zizmorcore/zizmor | Scan action workflows |
| Spec delta concepts | Fission-AI/OpenSpec | Extract concept without doubling methodology |
| Multi-harness configuration | doidor/agentrig | Evaluate ideas, not a foundational dependency |
| Evidence-oriented approaches | wihlarkop/proofcraft | Evaluate ideas, not a foundational dependency |


| File-oriented context organization | RinDig/Interpretable-Context-Methodology | **Core methodology**: five layers, canonical sources, bounded stage contracts and handoffs; adapt to AGENTS.md without vendoring upstream |

The catalog now has a tested, pinned instruction-only installer: see [skills.md](skills.md) and [skills.lock.json](../integrations/skills.lock.json). 'Selected' is not synonymous with executable dependencies installed or harness compatibility verified. The instruction-only importer does not run scripts.

Third-party popularity is not evidence of quality. Versions must be pinned before invoking executable packages or skills. No upstream code is vendored here.
