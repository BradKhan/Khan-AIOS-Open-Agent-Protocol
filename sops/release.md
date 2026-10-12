# Release and operations

After independent CI passes at current head and reviewers approve, perform the risk-tier approval gate. For critical deployments, rehearse rollback/restore and verify migrations against realistic data. Deploy with scoped credentials and record release SHA. Check real health, error reports and user-visible journeys. Open an issue for regressions and feed verified lessons into tests or skills, not speculative policy additions.
