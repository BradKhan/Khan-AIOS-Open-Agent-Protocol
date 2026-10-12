# Quality gates

The quality workflow tests Open ASS on Python 3.11 and 3.13, exercising the full suite and a real stdio MCP connection from the **official Python SDK v2.3.0**. This catches protocol bugs that internal JSON-RPC tests alone cannot. The SDK is only required in CI, not when copying the template.

A separately pinned **zizmor 1.30.1** offline scanner audits workflows for high-severity risks. The local security-baseline script remains a complementary check, not a security certification.

Checkout Actions are SHA-pinned to v7.0.1 (Node 24). GitHub administrator settings for required checks, reviews and template mode remain separate.

GitHub's previous privileged `pull_request_target` gate was removed following a high-severity zizmor finding; the normal PR path avoids privileged triggers and needs administrator-enforced independent review.
