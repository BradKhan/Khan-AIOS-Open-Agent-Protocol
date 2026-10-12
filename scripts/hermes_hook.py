#!/usr/bin/env python3
"""Opt-in Hermes pre_tool_call shell hook, following Hermes's documented wire format.

Heuristic defense in depth. Hooks are NOT a sandbox and may be bypassed.
"""
import json
import posixpath
import re
import sys

MAX_REQUEST = 100_000
SENSITIVE = frozenset({"POLICY.md", "SECURITY.md", "AGENTS.md", ".mcp.json",
                       "scripts/verify.py", "scripts/pr_gate.py",
                       "scripts/hermes_hook.py", "scripts/security_baseline.py"})
SENSITIVE_DIRS = ("config/", ".github/workflows/", ".claude/", ".codex/")
DANGEROUS = (
    re.compile(r"\bgit\s+push\b[^\n;]*\s--force(?:\s|=|$)", re.I),
    re.compile(r"\bgit\s+push\b[^\n;]*\s-f(?:\s|$)", re.I),
    re.compile(r"\bgit\s+reset\s+--hard(?:\s|$)", re.I),
    re.compile(r"\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+/(?:\s|$|[;&|])", re.I),
    re.compile(r"(?:\bcurl\b|\bwget\b)[^\n|]*\|\s*(?:bash|sh)\b", re.I)
)


def block(message):
    return {"action": "block", "message": message}


def normalize_path(path, cwd):
    """Relative or absolute path inside cwd; None when ownership is ambiguous."""
    if not isinstance(path, str) or not path or "\0" in path or "\\" in path:
        return None
    if not isinstance(cwd, str) or not cwd.startswith("/"):
        return None
    base = posixpath.normpath(cwd)
    absolute = posixpath.normpath(path if path.startswith("/") else posixpath.join(base, path))
    if absolute == base:
        return ""
    if not absolute.startswith(base.rstrip("/") + "/"):
        return None
    return absolute[len(base.rstrip("/")) + 1:]


def decision(payload):
    if not isinstance(payload, dict) or payload.get("hook_event_name") != "pre_tool_call":
        return block("Invalid Hermes pre_tool_call payload")
    tool, arguments = payload.get("tool_name"), payload.get("tool_input")
    if not isinstance(tool, str) or not isinstance(arguments, dict):
        return block("Missing Hermes tool information")
    if tool == "terminal":
        command = arguments.get("command")
        if not isinstance(command, str):
            return block("Missing terminal command")
        if any(pattern.search(command) for pattern in DANGEROUS):
            return block("Potentially destructive command; obtain out-of-band authorization")
    if tool in {"write_file", "patch"}:
        raw = arguments.get("path", arguments.get("file_path"))
        # Unknown cwd or ambiguous paths are escalated rather than permitted.
        path = normalize_path(raw, payload.get("cwd"))
        if path is None or path in SENSITIVE or path.startswith(SENSITIVE_DIRS):
            return {"action": "approve", "message": "Sensitive or ambiguous write; obtain explicit human approval"}
    return {}


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
        if len(raw) > MAX_REQUEST:
            raise ValueError("oversized hook input")
        print(json.dumps(decision(json.loads(raw))))
    except (ValueError, TypeError, UnicodeError):
        print(json.dumps(block("Could not parse Hermes hook request")))


if __name__ == "__main__":
    main()
