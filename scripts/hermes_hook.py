#!/usr/bin/env python3
"""Optional Hermes pre_tool_call guard (defense in depth, not a sandbox).

Consumes Hermes JSON hook payload on stdin and emits a documented hook directive.
Install only with explicit user consent and fail_closed: true.
"""
import json
import re
import sys

MAX_REQUEST = 100_000
SENSITIVE = (".github/workflows/", "POLICY.md", "SECURITY.md", "config/",
             "scripts/verify.py", "scripts/pr_gate.py", ".mcp.json")
DANGEROUS = [
    re.compile(r"\bgit\s+push\b[^\n;]*\s--force(?:\s|=|$)"),
    re.compile(r"\bgit\s+push\b[^\n;]*\s-f(?:\s|$)"),
    re.compile(r"\bgit\s+reset\s+--hard\b"),
    re.compile(r"\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+/(?:\s|$|[;&|])", re.I),
    re.compile(r"(?:\bcurl\b|\bwget\b)[^\n|]*\|\s*(?:bash|sh)\b", re.I)
]


def decision(payload):
    if not isinstance(payload, dict) or payload.get("hook_event_name") != "pre_tool_call":
        return {"decision": "block", "reason": "Malformed or non-pre-tool hook payload"}
    tool = payload.get("tool_name")
    arguments = payload.get("tool_input")
    if not isinstance(tool, str) or not isinstance(arguments, dict):
        return {"decision": "block", "reason": "Missing tool information"}
    if tool == "terminal":
        command = arguments.get("command")
        if not isinstance(command, str):
            return {"decision": "block", "reason": "Unknown shell command"}
        if any(pattern.search(command) for pattern in DANGEROUS):
            return {"decision": "block", "reason": "Destructive shell command requires out-of-band authorization"}
    if tool in ("write_file", "patch"):
        path = arguments.get("path") or arguments.get("file_path")
        if not isinstance(path, str):
            return {"action": "approve", "message": "Unknown write path; obtain explicit approval"}
        if any(path == item or path.startswith(item) for item in SENSITIVE):
            return {"action": "approve", "message": "Sensitive repository policy path; obtain explicit owner approval"}
    return {}


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
        if len(raw) > MAX_REQUEST:
            raise ValueError("Hook request too large")
        data = json.loads(raw)
        print(json.dumps(decision(data)))
    except (ValueError, TypeError, UnicodeError):
        print(json.dumps({"decision": "block", "reason": "Cannot evaluate tool request"}))


if __name__ == "__main__":
    main()
