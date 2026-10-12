#!/usr/bin/env python3
"""Read-only MCP stdio server exposing Open ASS context, roles and skills.

No shell, network, file mutation or elevated credentials. Not a policy enforcement
boundary: the host must still constrain tool/agent permissions.
"""
import json
import sys

try:
    from scripts import agents, context, skills
except ModuleNotFoundError:
    import agents, context, skills

VERSION = "2025-06-18"
TOOLS = [
    {"name": "openass_context_plan", "description": "List the exact selected context files and SHA-256 hashes for a stage, without reading their contents into the prompt.",
     "inputSchema": {"type": "object", "properties": {"stage": {"type": "string", "enum": sorted(context.MANDATORY_STAGES)},
                                                       "working": {"type": "array", "items": {"type": "string"}, "maxItems": 30}},
                     "required": ["stage"], "additionalProperties": False}},
    {"name": "openass_agent_plan", "description": "Inspect a bounded specialist role and task context handoff. This grants no permissions.",
     "inputSchema": {"type": "object", "properties": {"role": {"type": "string"},
                                                       "working": {"type": "array", "items": {"type": "string"}, "maxItems": 30}},
                     "required": ["role"], "additionalProperties": False}},
    {"name": "openass_skill_profiles", "description": "List curated skill profiles and pinned skill identifiers. Does not install or execute anything.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}}
]


def handle(request):
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
        raise ValueError("invalid JSON-RPC envelope")
    method = request.get("method")
    params = request.get("params", {})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise ValueError("invalid request parameters")
    if method == "initialize":
        return {"protocolVersion": VERSION, "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "open-ass", "version": "0.4.0"}}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments", {})
        if not isinstance(args, dict):
            raise ValueError("tool arguments must be an object")
        expected = next((tool for tool in TOOLS if tool["name"] == name), None)
        if expected is None:
            return {"content": [{"type": "text", "text": "Unknown tool"}], "isError": True}
        permitted = set(expected["inputSchema"]["properties"])
        if set(args) - permitted:
            raise ValueError("unsupported tool arguments")
        if name == "openass_skill_profiles":
            result = {"profiles": skills.load()["profiles"], "installed": skills.audit()}
        elif name == "openass_context_plan":
            if not isinstance(args.get("stage"), str):
                raise ValueError("stage must be specified")
            result = context.plan(args["stage"], _working(args.get("working", [])))
        else:
            if not isinstance(args.get("role"), str):
                raise ValueError("role must be specified")
            result = agents.plan(args["role"], _working(args.get("working", [])))
        return {"content": [{"type": "text", "text": json.dumps(result, sort_keys=True)}], "isError": False}
    raise ValueError("method not found: " + str(method))


def _working(value):
    if not isinstance(value, list) or len(value) > 30 or any(not isinstance(x, str) for x in value):
        raise ValueError("working must be a list of at most 30 paths")
    return value


def dispatch(request):
    if not isinstance(request, dict):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
    if "id" not in request:
        return None  # notifications must not generate a response
    request_id = request["id"]
    try:
        return {"jsonrpc": "2.0", "id": request_id, "result": handle(request)}
    except (ValueError, KeyError, TypeError, OSError, context.ContextError, agents.AgentError, skills.SkillError) as e:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": str(e)}}


def serve(source=sys.stdin, destination=sys.stdout):
    for line in source:
        if len(line) > 1_048_576:
            destination.write(json.dumps({"jsonrpc": "2.0", "id": None, "error":
                                          {"code": -32600, "message": "Request too large"}}) + "\n")
            destination.flush()
            continue
        try:
            request = json.loads(line)
            result = dispatch(request)
        except (ValueError, TypeError, json.JSONDecodeError):
            result = {"jsonrpc": "2.0", "id": None,
                      "error": {"code": -32700, "message": "Invalid JSON"}}
        if result is not None:
            destination.write(json.dumps(result, separators=(",", ":")) + "\n")
            destination.flush()


if __name__ == "__main__":
    serve()
