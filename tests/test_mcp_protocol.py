"""MCP 2025-06-18 stdio and JSON-RPC contract tests."""
import io
import json
import unittest
from scripts import mcp_server

def packet(method, uid=1, params=None):
    return {"jsonrpc": "2.0", "id": uid, "method": method, "params": params or {}}

class MCPProtocolTests(unittest.TestCase):
    def test_negotiation_and_read_only_annotations(self):
        p = mcp_server.dispatch(packet("initialize",params={"protocolVersion": "2025-11-25"}))
        self.assertEqual(p["result"]["protocolVersion"], "2025-06-18")
        tools=mcp_server.dispatch(packet("tools/list"))["result"]["tools"]
        self.assertTrue(all(t["annotations"]["readOnlyHint"] is True for t in tools))
        self.assertTrue(all(t["annotations"]["destructiveHint"] is False for t in tools))

    def test_invalid_rpc_ids_and_envelope(self):
        for x in ([], None, {"jsonrpc":"1.0","id":1,"method":"ping"},
                  {"jsonrpc":"2.0","id":None,"method":"ping"},
                  {"jsonrpc":"2.0","id":True,"method":"ping"}):
            with self.subTest(request=x):
                self.assertEqual(mcp_server.dispatch(x)["error"]["code"],-32600)

    def test_unknown_method_returns_32601(self):
        self.assertEqual(mcp_server.dispatch(packet("execute/shell"))["error"]["code"],-32601)

    def test_pre_handshake_rejected(self):
        out=io.StringIO()
        mcp_server.serve(io.StringIO(json.dumps(packet("tools/list"))+"\n"),out)
        self.assertEqual(json.loads(out.getvalue())["error"]["code"],-32000)

    def test_requires_initialized_notification(self):
        requests=[packet("initialize"),packet("tools/list",uid=2),
                  {"jsonrpc":"2.0","method":"notifications/initialized"},packet("tools/list",uid=3)]
        out=io.StringIO()
        mcp_server.serve(io.StringIO("".join(json.dumps(p)+"\n" for p in requests)),out)
        replies=[json.loads(p) for p in out.getvalue().splitlines()]
        self.assertEqual(len(replies),3)
        self.assertEqual(replies[1]["error"]["code"],-32000)
        self.assertEqual(len(replies[2]["result"]["tools"]),3)

    def test_oversized_input_drained_without_losing_next_message(self):
        bad='{"jsonrpc":"2.0","id":1,"method":"ping","noise":"'+("x"*(mcp_server.MAX_LINE+42))+'"}\n'
        out=io.StringIO()
        mcp_server.serve(io.StringIO(bad+json.dumps(packet("initialize",uid=2))+"\n"),out)
        replies=[json.loads(p) for p in out.getvalue().splitlines()]
        self.assertEqual(replies[0]["error"]["code"],-32600)
        self.assertEqual(replies[1]["result"]["protocolVersion"],"2025-06-18")

    def test_path_escape_rejected(self):
        r=mcp_server.dispatch(packet("tools/call",params={"name":"openass_context_plan",
            "arguments":{"stage":"verify","working":["../../.ssh/id_rsa"]}}))
        self.assertEqual(r["error"]["code"],-32602)

if __name__=="__main__":
    unittest.main()
