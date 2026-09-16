"""A Jupyter kernel run inside a Docker container.

Approach: a connection file with free host ports is written on the host via
`jupyter_client.write_connection_file`; the container is started with
`--network host` (Linux only — Docker Desktop's host networking does not
expose container ports the same way, which is a known, documented
limitation) sharing a bind-mounted directory containing that file, then
`ipykernel_launcher` is run inside the container against it. Since the
container shares the host's network namespace, the ports in the
host-written connection file are directly reachable from the host without
any port-mapping bookkeeping.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from ..utils.errors import ProviderError
from .kernel_client import JupyterKernelBackend
from .runtime_backend import ExecutionResult, RuntimeBackend


def docker_available() -> tuple[bool, str | None]:
    if shutil.which("docker") is None:
        return False, "'docker' binary not found on PATH."
    try:
        subprocess.run(["docker", "info"], capture_output=True, timeout=10, check=True)
    except subprocess.CalledProcessError as exc:
        return False, f"'docker info' failed: {exc.stderr.decode(errors='replace')[-500:]}"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return False, f"docker daemon unreachable: {exc}"
    return True, None


class DockerJupyterBackend(RuntimeBackend):
    def __init__(self, image: str = "python:3.11-slim", install_ipykernel: bool = True, startup_timeout: float = 120):
        self.image = image
        self.install_ipykernel = install_ipykernel
        self.startup_timeout = startup_timeout
        self.container_name = f"colab-mcp-{uuid.uuid4().hex[:10]}"
        self._tmpdir: tempfile.TemporaryDirectory | None = None
        self._inner: JupyterKernelBackend | None = None

    def connect(self) -> None:
        available, reason = docker_available()
        if not available:
            raise ProviderError(f"Docker is not usable: {reason}")

        self._tmpdir = tempfile.TemporaryDirectory(prefix="colab_mcp_docker_")
        host_dir = Path(self._tmpdir.name)
        connection_file = host_dir / "kernel.json"

        from jupyter_client import write_connection_file

        write_connection_file(str(connection_file))

        launch_cmd = f"python -m ipykernel_launcher -f /shared/kernel.json"
        if self.install_ipykernel:
            launch_cmd = f"pip install --quiet ipykernel && {launch_cmd}"

        run_cmd = [
            "docker", "run", "-d", "--rm",
            "--name", self.container_name,
            "--network", "host",
            "-v", f"{host_dir}:/shared",
            self.image,
            "sh", "-c", launch_cmd,
        ]
        proc = subprocess.run(run_cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            raise ProviderError("Failed to start Docker container for kernel.", details=proc.stderr)

        self._inner = JupyterKernelBackend(connection_file=str(connection_file))
        self._wait_and_connect()

    def _wait_and_connect(self) -> None:
        deadline = time.monotonic() + self.startup_timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                self._inner.connect()
                return
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(1.0)
        self._teardown_container()
        raise ProviderError(
            "Docker-hosted kernel did not become ready in time.",
            details=str(last_error),
        )

    def _teardown_container(self) -> None:
        subprocess.run(["docker", "rm", "-f", self.container_name], capture_output=True, timeout=15)

    def disconnect(self) -> None:
        if self._inner is not None:
            self._inner.disconnect()
        self._teardown_container()
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None

    @property
    def is_connected(self) -> bool:
        return self._inner is not None and self._inner.is_connected

    def kernel_info(self) -> dict[str, Any]:
        return self._inner.kernel_info()

    def interrupt(self) -> None:
        subprocess.run(["docker", "exec", self.container_name, "sh", "-c", "kill -INT 1"], capture_output=True, timeout=10)

    def restart(self) -> None:
        self.disconnect()
        self.connect()

    def execute(self, code: str, timeout: float) -> ExecutionResult:
        return self._inner.execute(code, timeout)
