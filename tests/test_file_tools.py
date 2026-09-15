import base64

import pytest

from google_colab_mcp.tools.file_tools import register as register_file_tools
from google_colab_mcp.tools.registry import ToolRegistry
from google_colab_mcp.utils.errors import ExecutionError


def _registry():
    registry = ToolRegistry()
    register_file_tools(registry)
    return registry


# The FakeRuntimeBackend used by the `ctx` fixture doesn't emulate a real
# filesystem, so every remote_fs snippet it "executes" comes back without
# the __FS_RESULT__ marker these tools expect — which correctly surfaces as
# an ExecutionError. That's still a useful test: it proves each tool builds
# a snippet, sends it through the execution pipeline, and propagates errors
# instead of swallowing them. Real filesystem behavior is covered against a
# live kernel in test_integration_real_kernel.py.


def test_write_file_reaches_execution_pipeline(ctx):
    registry = _registry()
    with pytest.raises(ExecutionError):
        registry.get("colab_write_file").handler(ctx, {"path": "notes.txt", "content": "hi there"})
    session = ctx.session_manager.get_or_create_default()
    assert session.backend.execute_count >= 1


def test_upload_file_reaches_execution_pipeline(ctx):
    registry = _registry()
    payload = base64.b64encode(b"binary-data").decode()
    with pytest.raises(ExecutionError):
        registry.get("colab_upload_file").handler(ctx, {"path": "blob.bin", "content_base64": payload})


def test_list_files_reaches_execution_pipeline(ctx):
    registry = _registry()
    with pytest.raises(ExecutionError):
        registry.get("colab_list_files").handler(ctx, {"path": ""})


def test_create_directory_reaches_execution_pipeline(ctx):
    registry = _registry()
    with pytest.raises(ExecutionError):
        registry.get("colab_create_directory").handler(ctx, {"path": "new_dir"})
