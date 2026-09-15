"""Confirms the MCP server object builds and exposes the expected handlers,
without needing a real stdio transport connection."""
from google_colab_mcp.context import ServerContext
from google_colab_mcp.server.app import build_mcp_server


def test_build_mcp_server_registers_handlers(tmp_settings):
    ctx = ServerContext.build(tmp_settings)
    try:
        server = build_mcp_server(ctx)
        assert server.name == "google-colab-mcp"
        handler_names = {cls.__name__ for cls in server.request_handlers}
        for expected in (
            "ListToolsRequest",
            "CallToolRequest",
            "ListResourcesRequest",
            "ReadResourceRequest",
            "ListPromptsRequest",
            "GetPromptRequest",
        ):
            assert expected in handler_names
    finally:
        ctx.shutdown()
