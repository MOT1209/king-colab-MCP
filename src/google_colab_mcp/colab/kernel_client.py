"""Jupyter-protocol backend.

Two modes:
  - `connection_file` set: attach to an already-running kernel (e.g. one a
    Colab "local runtime" session or any Jupyter kernel gateway exposes).
  - `connection_file` unset: launch and own a local kernel via
    `jupyter_client.KernelManager` — used for local development, tests, and
    any Jupyter-compatible sandbox that doesn't require a remote connection.
"""
from __future__ import annotations

import queue
import time
from typing import Any

from ..utils.errors import ConnectionError_, ExecutionTimeoutError, RuntimeUnavailableError
from .runtime_backend import ExecutionResult, RuntimeBackend


class JupyterKernelBackend(RuntimeBackend):
    def __init__(self, connection_file: str | None = None, kernel_name: str = "python3"):
        self.connection_file = connection_file
        self.kernel_name = kernel_name
        self._km = None
        self._kc = None
        self._owns_kernel = connection_file is None

    def connect(self) -> None:
        try:
            from jupyter_client import KernelManager
            from jupyter_client.blocking import BlockingKernelClient
        except ImportError as exc:  # pragma: no cover
            raise ConnectionError_(
                "jupyter_client is not installed.",
                details=str(exc),
                suggestion="pip install jupyter-client",
            ) from exc

        try:
            if self.connection_file:
                self._kc = BlockingKernelClient(connection_file=self.connection_file)
                self._kc.load_connection_file()
                self._kc.start_channels()
            else:
                self._km = KernelManager(kernel_name=self.kernel_name)
                self._km.start_kernel()
                self._kc = self._km.client()
                self._kc.start_channels()
            self._kc.wait_for_ready(timeout=30)
        except Exception as exc:
            raise ConnectionError_(
                "Failed to connect to the Jupyter/Colab kernel runtime.",
                details=str(exc),
            ) from exc

    def disconnect(self) -> None:
        if self._kc is not None:
            try:
                self._kc.stop_channels()
            except Exception:
                pass
        if self._owns_kernel and self._km is not None:
            try:
                self._km.shutdown_kernel(now=True)
            except Exception:
                pass
        self._kc = None
        self._km = None

    @property
    def is_connected(self) -> bool:
        return self._kc is not None and self._kc.is_alive()

    def kernel_info(self) -> dict[str, Any]:
        if not self.is_connected:
            raise RuntimeUnavailableError("No kernel is connected.")
        reply = self._kc.kernel_info()
        msg = self._kc.get_shell_msg(timeout=30)
        return msg.get("content", {})

    def interrupt(self) -> None:
        if self._km is not None:
            self._km.interrupt_kernel()
        elif self._kc is not None:
            self._kc.stop_channels()

    def restart(self) -> None:
        if self._km is None:
            raise RuntimeUnavailableError(
                "Cannot restart a kernel this backend does not own (attached via connection_file).",
            )
        self._km.restart_kernel(now=True)
        self._kc = self._km.client()
        self._kc.start_channels()
        self._kc.wait_for_ready(timeout=30)

    def execute(self, code: str, timeout: float) -> ExecutionResult:
        if not self.is_connected:
            raise RuntimeUnavailableError("No kernel is connected. Call colab_get_runtime to check status.")

        result = ExecutionResult()
        msg_id = self._kc.execute(code, allow_stdin=False)
        deadline = time.monotonic() + timeout

        stdout_parts: list[str] = []
        stderr_parts: list[str] = []

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                result.timed_out = True
                raise ExecutionTimeoutError(
                    f"Execution exceeded timeout of {timeout}s.",
                    details="".join(stdout_parts)[-2000:],
                )
            try:
                msg = self._kc.get_iopub_msg(timeout=min(remaining, 1.0))
            except queue.Empty:
                continue

            if msg.get("parent_header", {}).get("msg_id") != msg_id:
                continue

            msg_type = msg["header"]["msg_type"]
            content = msg["content"]

            if msg_type == "stream":
                if content.get("name") == "stdout":
                    stdout_parts.append(content.get("text", ""))
                else:
                    stderr_parts.append(content.get("text", ""))
            elif msg_type in ("execute_result", "display_data"):
                data = content.get("data", {})
                if msg_type == "execute_result":
                    result.result_repr = data.get("text/plain")
                    result.execution_count = content.get("execution_count")
                else:
                    result.display_data.append(data)
            elif msg_type == "error":
                result.error = {
                    "ename": content.get("ename"),
                    "evalue": content.get("evalue"),
                    "traceback": content.get("traceback", []),
                }
            elif msg_type == "status" and content.get("execution_state") == "idle":
                break

        result.stdout = "".join(stdout_parts)
        result.stderr = "".join(stderr_parts)
        return result
