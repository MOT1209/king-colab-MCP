from dataclasses import replace

from google_colab_mcp.server.protocol import dispatch_tool_call
from google_colab_mcp.tools.registry import build_default_registry


def test_dispatch_unknown_tool_returns_structured_error(ctx):
    registry = build_default_registry()
    payload = dispatch_tool_call(ctx, registry, "colab_does_not_exist", {})
    assert payload["success"] is False
    assert payload["error"]["type"] == "unknown_tool_error"


def test_dispatch_success_wraps_result(ctx):
    registry = build_default_registry()
    payload = dispatch_tool_call(ctx, registry, "colab_execute_code", {"code": "print('x')"})
    assert payload["success"] is True
    assert payload["result"]["stdout"] == "hello\n"


def test_dispatch_execution_error_is_structured(ctx):
    registry = build_default_registry()
    payload = dispatch_tool_call(ctx, registry, "colab_execute_code", {"code": "RAISE_ERROR"})
    assert payload["success"] is False
    assert payload["error"]["type"] == "execution_error"
    assert "boom" in payload["error"]["details"] or "ValueError" in payload["error"]["message"]


def test_dispatch_denied_tool_is_authorization_error(ctx):
    ctx.settings = replace(ctx.settings, denied_tools=["colab_execute_code"])
    registry = build_default_registry()
    payload = dispatch_tool_call(ctx, registry, "colab_execute_code", {"code": "1"})
    assert payload["success"] is False
    assert payload["error"]["type"] == "authorization_error"


def test_dispatch_never_leaks_secrets_in_error_details(ctx):
    registry = build_default_registry()
    payload = dispatch_tool_call(
        ctx, registry, "colab_execute_code", {"code": "RAISE_ERROR api_key=sk-1234567890abcdefghijklmno"}
    )
    assert "sk-1234567890abcdefghijklmno" not in str(payload)


def test_dispatch_unknown_tool_includes_retryable(ctx):
    registry = build_default_registry()
    payload = dispatch_tool_call(ctx, registry, "colab_does_not_exist", {})
    assert payload["success"] is False
    assert "retryable" in payload["error"]
    assert payload["error"]["retryable"] is False
