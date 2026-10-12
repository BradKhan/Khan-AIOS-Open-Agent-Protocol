# Evaluation plan

Choose 10-20 representative real feature and bug tasks, including at least three ambiguous requirements and three failure/recovery cases. Fix each starting SHA and maintain a held-out independent test suite.

Compare baseline agent against the same agent with the template and selected skills. Capture model/provider versions, token usage, retries, wall-clock time, compute cost, human interventions, acceptance test outcomes and independently discovered defects. Repeat nondeterministic runs and publish failures.

Primary metric: cost per independently accepted task, with correctness and safety as hard constraints. Do not claim a productivity gain before observing one.
