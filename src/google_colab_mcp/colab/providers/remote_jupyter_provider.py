"""A remote/self-hosted Jupyter kernel gateway — explicitly *not* claimed to be Colab.

Use this for any Jupyter-protocol-compatible runtime that isn't Google
Colab: a JupyterHub-managed kernel, a self-hosted kernel gateway, etc.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ..kernel_client import JupyterKernelBackend
from ..runtime_backend import RuntimeBackend
from .base import ProviderDiscoveryResult, RuntimeProvider


class RemoteJupyterProvider(RuntimeProvider):
    provider_id: ClassVar[str] = "remote_jupyter"

    def discover(self) -> ProviderDiscoveryResult:
        connection_file = self.config.get("connection_file")
        if not connection_file:
            return ProviderDiscoveryResult(
                available=False,
                reason="No 'connection_file' configured for the remote Jupyter kernel.",
            )
        if not Path(connection_file).exists():
            return ProviderDiscoveryResult(
                available=False,
                reason=f"connection_file does not exist: {connection_file}",
            )
        return ProviderDiscoveryResult(available=True, metadata={"connection_file": connection_file})

    def _create_backend(self) -> RuntimeBackend:
        return JupyterKernelBackend(connection_file=self.config["connection_file"])
