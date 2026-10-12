# Hermes pre-tool hook

Open ASS includes an optional **pre-tool-call** shell hook in `scripts/hermes_hook.py`, plus a reviewed example configuration at `integrations/hermes-hooks.example.yaml`. The hook accepts Hermes's documented JSON input and returns `decision: block` for a few known destructive commands or `action: approve` for sensitive repository policy writes.

To use it, explicitly consent to the shell hook in your Hermes profile, copy the example YAML into the relevant profile configuration, and replace the placeholder with an **absolute** path to a trusted checkout. Set `fail_closed: true` as in the example. Test it with the Hermes version you actually run (`hermes hooks test`, when available).

This is **heuristic defense in depth**. It cannot correctly interpret arbitrary shell commands, prevent every destructive operation, or replace an OS/container sandbox. A model can call other tools, and hook consent is scoped by Hermes. Unapproved hooks are skipped. For actual permissions use least-privileged tokens, filesystem/sandbox isolation, GitHub rulesets and independent review.

No agent-level hooks are installed automatically. Ordinary Git hooks can be installed separately with `python3 scripts/openass.py hooks install`.
