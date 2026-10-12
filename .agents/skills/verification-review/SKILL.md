---
name: verification-review
description: Independently review a pull request against accepted criteria, current-head CI, security and meaningful regression coverage.
---

# Independent review

1. Read accepted issue/spec, PR diff and affected code. Prefer a reviewer without the implementer's scratchpad.
2. Confirm current PR head SHA and independently query required GitHub checks.
3. Inspect negative paths, tests, unintended scope, security and recoverability.
4. Distinguish verified facts, unverified claims and blocked checks.
5. Give precise file/reproduction evidence for each blocker.
6. Do not approve your own code, waive required tests or change risk classification without authorization.
