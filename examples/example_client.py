"""Minimal example: a generic MCP client talking to google-colab-mcp over stdio.

This uses the official `mcp` client SDK only — nothing here is specific to
any particular agent framework, which is the point: any MCP client can
drive this server this way.

Run with:  python examples/example_client.py
"""
from __future__ import annotations

import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server_params = StdioServerParameters(command="google-colab-mcp", args=[])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools][:10], "...")

            result = await session.call_tool(
                "colab_execute_code",
                {"code": "import sys\nprint('Hello from', sys.version)\n2 + 2"},
            )
            print(json.dumps(json.loads(result.content[0].text), indent=2))

            runtime = await session.call_tool("colab_get_runtime", {})
            print(json.dumps(json.loads(runtime.content[0].text), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
