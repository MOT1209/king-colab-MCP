import base64

import pytest

from google_colab_mcp.colab.execution_manager import ExecutionManager
from google_colab_mcp.colab.remote_fs import RemoteFileManager
from google_colab_mcp.utils.errors import ResourceExhaustedError


def test_execution_output_truncated_over_limit(ctx):
    small_execution_manager = ExecutionManager(ctx.session_manager, max_output_bytes=3)
    result = small_execution_manager.run("print('hello')", None, timeout=10)
    assert result["output_truncated"] is True
    assert "truncated" in result["stdout"]


def test_execution_output_not_truncated_under_limit(ctx):
    result = ctx.execution_manager.run("print('hi')", None, timeout=10)
    assert result["output_truncated"] is False


def test_remote_upload_rejects_oversized_payload(ctx):
    small_fs = RemoteFileManager(ctx.execution_manager, "/content/mcp_workspace", max_file_size_bytes=10)
    payload = base64.b64encode(b"x" * 1000).decode()
    with pytest.raises(ResourceExhaustedError):
        small_fs.upload_file("big.bin", payload)
