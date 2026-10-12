#!/usr/bin/env python3
"""Read-only MCP stdio server exposing Open ASS context, roles and skills.

No shell, network, file mutation or elevated credentials. Not a policy enforcement
boundary: the host must still constrain tool/agent permissions.
"""
import json
import sys

MAX_LINE = 1_048_576

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

for tool in TOOLS:
    tool["annotations"] = {"readOnlyHint": True, "destructiveHint": False,
                           "idempotentHint": True, "openWorldHint": False}


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
        requested = params.get("protocolVersion")
        if requested is not None and not isinstance(requested, str):
            raise ValueError("protocolVersion must be a string")
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
    if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
    if "id" not in request:
        return None  # notifications must not generate a response
    if request["id"] is None or isinstance(request["id"], bool) or not isinstance(request["id"], (str, int)):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request id"}}
    request_id = request["id"]
    try:
        return {"jsonrpc": "2.0", "id": request_id, "result": handle(request)}
    except (ValueError, KeyError, TypeError, OSError, context.ContextError, agents.AgentError, skills.SkillError) as e:
        message = str(e)
        code = -32601 if message.startswith("method not found: ") else -32602
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def serve(source=sys.stdin, destination=sys.stdout):
    """Legacy MCP 2025-06-18 lifecycle; strict one-line JSON-RPC stdio."""
    initialized = False
    awaiting_confirmation = False
    while True:
        line = source.readline(MAX_LINE + 1)
        if not line:
            break
        if len(line) > MAX_LINE:
            while not line.endswith("\n"):
                line = source.readline(MAX_LINE + 1)
                if not line:
                    break
            response = {"jsonrpc": "2.0", "id": None,
                        "error": {"code": -32600, "message": "Request too large"}}
        else:
            try:
                request = json.loads(line)
                method = request.get("method") if isinstance(request, dict) else None
                if method == "initialize":
                    response = dispatch(request)
                    awaiting_confirmation = "result" in response
                elif method == "notifications/initialized":
                    if awaiting_confirmation and isinstance(request, dict) and request.get("jsonrpc") == "2.0":
                        initialized = True
                    response = None
                elif not initialized:
                    if isinstance(request, dict) and "id" not in request:
                        response = None
                    else:
                        response = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                                    "error": {"code": -32000, "message": "MCP initialize handshake required"}}
                else:
                    response = dispatch(request)
            except (ValueError, TypeError, json.JSONDecodeError):
                response = {"jsonrpc": "2.0", "id": None,
                            "error": {"code": -32700, "message": "Invalid JSON"}}
        if response is not None:
            destination.write(json.dumps(response, separators=(",", ":")) + "\n")
            destination.flush()


if __name__ == "__main__":
    serve()
