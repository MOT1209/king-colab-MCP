from google_colab_mcp.tools.execution_tools import register as register_execution_tools
from google_colab_mcp.tools.registry import ToolRegistry
from google_colab_mcp.utils.errors import ExecutionError

import pytest


def _registry():
    registry = ToolRegistry()
    register_execution_tools(registry)
    return registry


def test_execute_code_success(ctx):
    registry = _registry()
    spec = registry.get("colab_execute_code")
    result = spec.handler(ctx, {"code": "print('hi')\n2 + 2"})
    assert result["stdout"] == "hello\n"
    assert result["result"] == "2"
    assert "session_id" in result


def test_execute_code_error_raises_execution_error(ctx):
    registry = _registry()
    spec = registry.get("colab_execute_code")
    with pytest.raises(ExecutionError):
        spec.handler(ctx, {"code": "RAISE_ERROR"})


def test_stop_execution_marks_interrupted(ctx):
    registry = _registry()
    spec = registry.get("colab_stop_execution")
    result = spec.handler(ctx, {})
    assert result["interrupted"] is True
    session = ctx.session_manager.get(result["session_id"])
    assert session.backend.interrupted is True
