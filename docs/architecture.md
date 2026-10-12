# Architecture

GitHub owns project requirements, source, accepted architecture decisions, issues, PRs and versioned skill references. CI runs independent checks against the actual commit SHA.

An optional orchestrator (Paperclip or equivalent) manages task leases, budgets and retries, not acceptance criteria. An optional worker (Hermes, Codex, OpenBot, Claude) executes in isolated workspaces. Cloudflare may provide webhook ingestion and delivery. External memory may provide contextual recall, but must respect permissions and cannot silently override approved specs.

## Lifecycle owners

- Requirements and feature-spec analysis: optional GitHub Spec Kit.
- Debugging, TDD, isolation and engineering review: selected Superpowers practices.
- Code/security review: project CI plus independent reviewer; optionally reviewed Sentry skills.
- UI work: optionally Impeccable, Vercel guidelines and Playwright.
- Model behavior evaluations: optionally Promptfoo.
- Merge acceptance: independent GitHub checks and authorized reviewer.

One accepted plan per change, not parallel competing planning systems. Fast work skips heavyweight specification where risk permits.

## Completion

An agent may submit evidence JSON, but self-reported green checks are not trusted attestation. Check the actual PR head SHA, CI run, review state and policy. Never treat missing application tests as success.

## Limits

No database, model API, hosted coordination, prompt-evaluation service, or special skills installer is required for the default template. Compatibility claims require test runs against named harness revisions.

## Interpretable context (ICM)

The core's context architecture follows ICM's orientation → routing → stage → canonical references → working artifacts layers. The only authoritative routing registry is `context/routes.json`; `CONTEXT.md` is its human entrypoint. Each stage declares Inputs, Process, Outputs, Permissions, and References. This is a context/handoff method, not another scheduler or specification engine. See `docs/context-methodology.md`. Context manifests report selected file hashes without pretending to prove what an LLM consumed.
