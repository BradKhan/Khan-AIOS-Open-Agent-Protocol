# MCP protocol support

The built-in read-only stdio MCP server supports the **2025-06-18 handshake protocol**, including initialize, notifications/initialized, tools/list and JSON-RPC 2.0. Read-only annotations, request limits, invalid request IDs, lifecycle ordering and escaped file paths are tested.

The upstream MCP specification now also includes a **2026-07-28 stateless lifecycle**. Open ASS does not yet support that new lifecycle or remote HTTP transport. Use hosts that negotiate the older handshake; do not advertise modern-protocol compatibility without SDK tests.

See [harness integration](harnesses.md) for setup. This server never grants shell, arbitrary filesystem, GitHub write, or network tools.
