#!/usr/bin/env python3
"""Independently inspect GitHub PR head, checks and human approval via REST.

This is a read-only audit command. It cannot approve, merge or deploy changes.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


class AttestError(ValueError):
    pass


def api_get(path, token=None):
    if not re.fullmatch(r"/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:pulls/[0-9]+(?:/reviews)?|commits/[0-9a-f]{40}/check-runs)(?:\?per_page=100)?", path):
        raise AttestError("unapproved GitHub API path")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "open-ass-evidence/1",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token is None:
        token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        if response.url.split("/")[2] != "api.github.com":
            raise AttestError("unsafe API redirect")
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise AttestError("GitHub API response exceeds limit")
    return json.loads(raw)


try:
    from scripts import release_policy
except ModuleNotFoundError:
    import release_policy

DEFAULT_REQUIRED = release_policy.read()["checks"]


def evaluate(pull, checks, reviews, required, human_review=True, trusted_app=None):
    if not isinstance(pull, dict) or pull.get("state") != "open":
        raise AttestError("PR must be open")
    head = pull.get("head", {}).get("sha")
    if not isinstance(head, str) or not re.fullmatch("[0-9a-f]{40}", head):
        raise AttestError("PR head SHA missing")
    if not isinstance(checks, list) or not isinstance(reviews, list):
        raise AttestError("GitHub checks/reviews missing")
    found = {}
    for item in checks:
        if item.get("head_sha") != head:
            continue
        if trusted_app is not None and (item.get("app") or {}).get("slug") != trusted_app:
            continue
        name = item.get("name")
        if name not in found:  # GitHub returns newest runs first
            found[name] = item
    missing = [name for name in required if name not in found or found[name].get("status") != "completed" or found[name].get("conclusion") != "success"]
    if missing:
        raise AttestError("required checks not successful at head " + head[:12] + ": " + ", ".join(missing))
    accepted = []
    if human_review:
        latest = {}
        for entry in sorted(reviews, key=lambda r: r.get("submitted_at") or ""):
            reviewer = entry.get("user") or {}
            login = reviewer.get("login")
            if login:
                latest[login.casefold()] = entry
        author = str(pull.get("user", {}).get("login", "")).casefold()
        for login, review in latest.items():
            reviewer = review.get("user") or {}
            if (login != author and reviewer.get("type", "User") == "User"
                    and not login.endswith("[bot]") and review.get("state") == "APPROVED"
                    and review.get("commit_id") == head):
                accepted.append(login)
        if not accepted:
            raise AttestError("no independent human approval on the current PR head")
    return {"pr": pull.get("number"), "head_sha": head, "verified_checks": sorted(required),
            "current_head_approvers": sorted(accepted),
            "note": "GitHub evidence checked; semantic acceptance and deploy authorization are separate."}


def inspect(repo, number, checks, require_review=True, fetch=api_get):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or number <= 0:
        raise AttestError("invalid repository or PR number")
    base = f"/repos/{repo}"
    pr = fetch(base + f"/pulls/{number}")
    head = pr.get("head", {}).get("sha")
    if not isinstance(head, str) or not re.fullmatch("[a-f0-9]{40}", head):
        raise AttestError("invalid PR head")
    runs = fetch(base + f"/commits/{head}/check-runs?per_page=100")
    if runs.get("total_count", 0) > len(runs.get("check_runs", [])):
        raise AttestError("check results paginated; refusing incomplete attestation")
    reviews = fetch(base + f"/pulls/{number}/reviews?per_page=100") if require_review else []
    if len(reviews) == 100 and require_review:
        raise AttestError("review results may be paginated; refusing incomplete attestation")
    return evaluate(pr, runs["check_runs"], reviews, checks, require_review,
                    trusted_app="github-actions")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", required=True)
    p.add_argument("--pr", type=int, required=True)
    p.add_argument("--require", action="append", default=None,
                   help="Override default required check names; supply each needed check")
    p.add_argument("--no-human-review", action="store_true", help="Diagnostic only; never authorizes merge")
    args = p.parse_args()
    try:
        print(json.dumps(inspect(args.repo, args.pr, set(args.require or DEFAULT_REQUIRED),
                                 not args.no_human_review), indent=2))
    except (AttestError, KeyError, ValueError, TypeError, urllib.error.URLError) as exc:
        print("attest: " + str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
