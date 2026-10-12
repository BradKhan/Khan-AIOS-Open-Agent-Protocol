# First verified application PR

1. Install Python 3.11+ and requirements-dev.txt.
2. Run python3 scripts/verify.py. Output must explicitly say TEMPLATE SELF-TEST ONLY.
3. Copy the repository and fill in PROJECT.md and ARCHITECTURE.md.
4. Run python3 scripts/init_project.py --name my-app --app-check python3 -m pytest -q, substituting actual checks. Use --tier critical and --security-check if required.
5. Run just verify or python3 scripts/verify.py after application code exists.
6. File an issue, implement with an agent or by hand, and open a PR linked to the issue.
7. Configure protected main branch, mandatory checks and independent reviewer outside the template through GitHub Settings.

Passing template tests never claims to verify an application's functionality, UX, deployment or security.
