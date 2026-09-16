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


def test_real_colab_provider_rejects_non_colab_kernel():
    """The whole point of ColabProvider: a plain local kernel must never be
    reported as genuine Colab, even though it speaks the same protocol."""
    from jupyter_client import KernelManager

    from google_colab_mcp.colab.providers import ColabProvider
    from google_colab_mcp.utils.errors import ColabUnavailableError

    km = KernelManager(kernel_name="python3")
    try:
        km.start_kernel()
    except Exception as exc:
        pytest.skip(f"no local Jupyter kernel available: {exc}")

    try:
        provider = ColabProvider({"connection_file": km.connection_file})
        with pytest.raises(ColabUnavailableError):
            provider.connect()
        assert provider.verification["is_genuine_colab"] is False
    finally:
        km.shutdown_kernel(now=True)


def test_real_local_jupyter_provider_connects_and_executes():
    from google_colab_mcp.colab.providers import LocalJupyterProvider

    provider = LocalJupyterProvider({})
    try:
        backend = provider.connect()
    except Exception as exc:
        pytest.skip(f"no local Jupyter kernel available: {exc}")

    try:
        result = backend.execute("21 * 2", timeout=15)
        assert result.result_repr == "42"
    finally:
        backend.disconnect()


def test_real_runtime_info(real_session_manager):
    from google_colab_mcp.colab.runtime_manager import RuntimeManager

    runtime_manager = RuntimeManager(ExecutionManager(real_session_manager))
    info = runtime_manager.get_runtime_info()
    assert "python_version" in info
    cpu = runtime_manager.get_cpu_info()
    assert "logical_cores" in cpu
