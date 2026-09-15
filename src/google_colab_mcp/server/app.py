"""MCP server bootstrap: wires config, security, Colab managers, and the
tool/resource/prompt registries into a running `mcp.server.lowlevel.Server`,
then serves it over stdio (the default MCP transport for local clients).

This module has zero knowledge of any specific AI agent or framework — it
only speaks the MCP protocol, over whichever transport `transport.py`
selects.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

import mcp.types as types
from mcp.server.lowlevel import Server

from .. import __version__
from ..config import get_settings
from ..context import ServerContext
from ..logging.setup import configure_logging, get_logger
from ..resources.prompts import PROMPT_DEFS, get_prompt as _get_prompt_content
from ..resources.resources import RESOURCE_DEFS, read_resource as _read_resource
from ..tools.registry import build_default_registry
from .protocol import dispatch_tool_call
from .transport import run_sse, run_stdio

logger = get_logger("app")


def build_mcp_server(ctx: ServerContext) -> Server:
    server = Server("google-colab-mcp", version=__version__)
    registry = build_default_registry()

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(name=spec.name, description=spec.description, inputSchema=spec.input_schema)
            for spec in registry.all()
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        payload = dispatch_tool_call(ctx, registry, name, arguments)
        return [types.TextContent(type="text", text=json.dumps(payload, indent=2, default=str))]

    @server.list_resources()
    async def list_resources() -> list[types.Resource]:
        return [
            types.Resource(
                uri=r["uri"], name=r["name"], description=r["description"], mimeType=r["mime_type"]
            )
            for r in RESOURCE_DEFS
        ]

    @server.read_resource()
    async def read_resource(uri) -> str:
        return _read_resource(ctx, str(uri))

    @server.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        return [
            types.Prompt(
                name=p["name"],
                description=p["description"],
                arguments=[types.PromptArgument(**a) for a in p["arguments"]],
            )
            for p in PROMPT_DEFS
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
        messages = _get_prompt_content(name, arguments or {})
        return types.GetPromptResult(
            description=next(p["description"] for p in PROMPT_DEFS if p["name"] == name),
            messages=[
                types.PromptMessage(role=m["role"], content=types.TextContent(**m["content"]))
                for m in messages
            ],
        )

    return server


def main() -> None:
    parser = argparse.ArgumentParser(prog="google-colab-mcp", description="Standalone Google Colab MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default=None, help="Override MCP_TRANSPORT.")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    transport = args.transport or settings.mcp_transport

    ctx = ServerContext.build(settings)
    server = build_mcp_server(ctx)

    logger.info(f"Starting google-colab-mcp v{__version__} over {transport} transport.")
    try:
        if transport == "stdio":
            asyncio.run(run_stdio(server))
        elif transport == "sse":
            asyncio.run(run_sse(server, settings.mcp_host, settings.mcp_port))
        else:
            print(f"Unknown transport: {transport}", file=sys.stderr)
            sys.exit(1)
    finally:
        ctx.shutdown()


if __name__ == "__main__":
    main()
