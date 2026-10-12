# Optional orchestrator contract

Canonical task identity: owner/repo#number. GitHub owns issue intent, accepted specifications and PR review. Paperclip or another scheduler owns temporary leases, execution attempts, budgets and allocation.

State progression: ready -> claimed -> running -> pr_open -> awaiting_checks -> accepted; alternative results blocked, failed or cancelled.

1. Acquire an atomic lease with an expiration timestamp and a unique run ID.
2. Reconcile GitHub issue/PR status and immutable base SHA before work. Do not start a duplicate run if an active lease exists.
3. Execute in isolated workspace; never change issue acceptance criteria without review.
4. Publish PR link, head SHA, log artifacts, and failure information back to GitHub.
5. Query GitHub for real required checks and approvals at the current head SHA before declaring complete.
6. Retry only retryable failures under spending and attempt ceilings. Recover orphaned tasks after leases expire.

Webhook deliveries can repeat: authenticate with GitHub HMAC, deduplicate delivery IDs, and make all transitions idempotent. Enforce credentials and authorization at the executor, not only in task JSON.
