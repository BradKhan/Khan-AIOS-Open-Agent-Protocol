# Product-quality pipeline

Run python3 scripts/openass.py quality plan to see the applicable role/skill sequence. Static HTML checking is executable: quality html tests/fixtures/valid-page.html passes, while invalid-page.html fails because it lacks accessible labels, an image alternative and suitable headings.

The product-quality evidence gate requires three separate files with SHA-256 fingerprints: a real browser checks JSON report (passed=true and nonempty checks), an accessibility JSON report (violations=[] and nonempty passes), and a PNG screenshot. It also requires a passing application-test exit code, the exact PR head SHA, and a named copy reviewer. Run quality evidence path/to/manifest.json to verify that the files exist and match their hashes. These artifacts must come from real tools; fabricating them defeats the purpose. Their existence alone is not an independent audit or semantic design score.

Taste -> implementation -> Impeccable -> Vercel guidelines -> Playwright/browser and accessibility -> Humanizer -> independent acceptance is the default web path. Backend-only tasks skip visual steps. Design and writing skills are instruction bundles unless separate executables and runtime integrations are installed.

The HTML checker is intentionally narrow; it does not measure contrast, visual taste or runtime interactions. Those require browser evidence, accessibility tooling and human review.
