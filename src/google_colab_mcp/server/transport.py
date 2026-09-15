"""Pluggable MCP transports.

`stdio` is the default and what every local MCP client (Claude Code, Cursor,
VS Code, custom agents) speaks out of the box. `sse` is provided for
network-reachable deployments (e.g. a containerized server multiple agents
share). Adding a new transport means adding one function here with the same
`(server, ...) -> Awaitable[None]` shape — nothing else in the codebase
needs to change.
"""
from __future__ import annotations

from mcp.server.lowlevel import Server


async def run_stdio(server: Server) -> None:
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def run_sse(server: Server, host: str, port: int) -> None:
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    import uvicorn

    transport = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with transport.connect_sse(request.scope, request.receive, request._send) as (r, w):
            await server.run(r, w, server.create_initialization_options())

    app = Starlette(routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=transport.handle_post_message),
    ])
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    await uvicorn.Server(config).serve()


TRANSPORTS = {"stdio": run_stdio, "sse": run_sse}
