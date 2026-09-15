"""End-to-end test against a real, locally-launched Jupyter kernel (ipykernel).

Skipped automatically if ipykernel/jupyter_client can't actually start a
kernel in this environment (e.g. a minimal CI image without a kernelspec).
"""
from __future__ import annotations

import pytest

from google_colab_mcp.colab.session_manager import SessionManager
from google_colab_mcp.colab.execution_manager import ExecutionManager


@pytest.fixture(scope="module")
def real_session_manager():
    manager = SessionManager()
    try:
        manager.get_or_create_default()
    except Exception as exc:
        pytest.skip(f"no local Jupyter kernel available: {exc}")
    yield manager
    manager.close_all()


def test_real_execute_code_roundtrip(real_session_manager):
    execution_manager = ExecutionManager(real_session_manager)
    result = execution_manager.run("print('integration ok')\n21 * 2", session_id=None, timeout=30)
    assert result["stdout"] == "integration ok\n"
    assert result["result"] == "42"


def test_real_execution_error_surfaces_traceback(real_session_manager):
    from google_colab_mcp.utils.errors import ExecutionError

    execution_manager = ExecutionManager(real_session_manager)
    with pytest.raises(ExecutionError) as excinfo:
        execution_manager.run("1 / 0", session_id=None, timeout=30)
    assert "ZeroDivisionError" in str(excinfo.value)


def test_real_remote_file_roundtrip(real_session_manager, tmp_path):
    from google_colab_mcp.colab.remote_fs import RemoteFileManager

    execution_manager = ExecutionManager(real_session_manager)
    remote_root = f"{tmp_path}/mcp_workspace"
    fs = RemoteFileManager(execution_manager, remote_root)

    fs.write_file("hello.txt", "remote content")
    read_back = fs.read_file("hello.txt")
    assert read_back["content"] == "remote content"

    listing = fs.list_files("")
    assert any(entry["name"] == "hello.txt" for entry in listing["entries"])

    fs.delete_file("hello.txt")
    listing_after = fs.list_files("")
    assert not any(entry["name"] == "hello.txt" for entry in listing_after["entries"])


def test_real_runtime_info(real_session_manager):
    from google_colab_mcp.colab.runtime_manager import RuntimeManager

    runtime_manager = RuntimeManager(ExecutionManager(real_session_manager))
    info = runtime_manager.get_runtime_info()
    assert "python_version" in info
    cpu = runtime_manager.get_cpu_info()
    assert "logical_cores" in cpu
