# Durable task lifecycle

Run tasks through python3 scripts/openass.py task. Its SQLite store lives in .openass/tasks.sqlite3 (untracked). Every transition runs under an IMMEDIATE transaction and requires the current revision. A stale actor cannot overwrite newer work. States: proposed, clarifying, ready, running, verifying, review, accepted, failed, cancelled. Retries are bounded; spending cannot exceed a stated cost ceiling. Each transition writes an event.

Example: task create feature-1 --issue 42 --criteria "The command exits zero on valid input" --budget-cents 500; task transition feature-1 ready --actor owner --expected-revision 0; task transition feature-1 start --actor engineer --expected-revision 1.

Acceptance requires an independent actor plus a matching current-head GitHub attestation; it cannot be obtained from a local flag in the CLI. This tracker **does not execute agents**, acquire remote leases, call LLM providers, merge branches, or automatically track spending; the caller must report costs and task events. The next harness adapter layer connects execution to this contract. Back up the database for durable operation on persistent hosts.
