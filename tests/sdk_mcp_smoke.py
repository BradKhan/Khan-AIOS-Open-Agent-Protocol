"""External SDK handshake against an actual Open ASS MCP subprocess.

Requires mcp==2.3.0 and installed framework dependencies.
"""
import asyncio
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]

async def main():
    server = StdioServerParameters(command=sys.executable,
        args=[str(ROOT/"scripts/mcp_server.py")], cwd=str(ROOT))
    async with Client(server) as client:
        tools = await client.list_tools()
        expected={"openass_agent_plan","openass_context_plan","openass_skill_profiles"}
        names = {tool.name for tool in tools.tools}
        assert names == expected, (names, expected)
        result=await client.call_tool("openass_agent_plan", {"role":"reviewer"})
        assert not result.is_error, result
        assert "reviewer" in str(result.content)
        print("OFFICIAL MCP SDK: subprocess handshake, discovery and tool call PASS")

if __name__ == "__main__":
    asyncio.run(main())
