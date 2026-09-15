from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import pytest

from google_colab_mcp.colab.runtime_backend import ExecutionResult, RuntimeBackend
from google_colab_mcp.colab.session_manager import SessionManager
from google_colab_mcp.config.settings import Settings
from google_colab_mcp.context import ServerContext


class FakeRuntimeBackend(RuntimeBackend):
    """Deterministic in-memory stand-in for a real Jupyter/Colab kernel, for fast unit tests."""

    def __init__(self, connection_file: str | None = None):
        self.connection_file = connection_file
        self._connected = False
        self.execute_count = 0
        self.interrupted = False
        self.restarted = False

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def kernel_info(self) -> dict[str, Any]:
        return {"implementation": "fake", "language_info": {"name": "python"}}

    def interrupt(self) -> None:
        self.interrupted = True

    def restart(self) -> None:
        self.restarted = True
        self.execute_count = 0

    def execute(self, code: str, timeout: float) -> ExecutionResult:
        self.execute_count += 1
        result = ExecutionResult()

        if "RAISE_ERROR" in code:
            extra = code.split("RAISE_ERROR", 1)[1].strip()
            evalue = f"boom {extra}".strip()
            result.error = {"ename": "ValueError", "evalue": evalue, "traceback": ["Traceback...", f"ValueError: {evalue}"]}
            return result

        if "__RUNTIME_INFO__" in code or code.strip().startswith("import json, sys, platform"):
            result.stdout = '__RUNTIME_INFO__{"python_version": "3.11.0", "platform": "fake", "cuda_available": false}\n'
            return result

        if "print" in code:
            result.stdout = "hello\n"
        result.result_repr = "2"
        result.execution_count = self.execute_count
        return result


@pytest.fixture
def tmp_settings(tmp_path):
    workspace = tmp_path / "workspace"
    artifacts = tmp_path / "artifacts"
    notebooks = tmp_path / "notebooks"
    audit = tmp_path / "logs" / "audit.log"
    settings = Settings(
        workspace_root=workspace,
        artifact_root=artifacts,
        notebook_root=notebooks,
        audit_log_path=audit,
        require_auth=False,
        max_requests_per_minute=1000,
    )
    settings.ensure_dirs()
    return settings


@pytest.fixture
def ctx(tmp_settings):
    context = ServerContext.build(tmp_settings)
    context.session_manager = SessionManager(backend_factory=lambda cf: FakeRuntimeBackend(cf))
    # ExecutionManager holds a reference to the *original* session_manager; rebuild it too.
    from google_colab_mcp.colab.execution_manager import ExecutionManager
    from google_colab_mcp.colab.notebook_manager import NotebookManager
    from google_colab_mcp.colab.remote_fs import RemoteFileManager
    from google_colab_mcp.colab.runtime_manager import RuntimeManager

    context.execution_manager = ExecutionManager(context.session_manager)
    context.runtime_manager = RuntimeManager(context.execution_manager)
    context.notebook_manager = NotebookManager(context.path_guard, context.execution_manager)
    context.remote_file_manager = RemoteFileManager(context.execution_manager, context.settings.remote_workspace_root)
    yield context
    context.shutdown()
