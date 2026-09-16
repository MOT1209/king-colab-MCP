"""A locally-launched Jupyter kernel — explicitly *not* claimed to be Colab.

The right provider for development, tests, and any sandboxed Python
execution need that doesn't require Colab's specific hardware.
"""
from __future__ import annotations

import importlib.util
from typing import ClassVar

from ..kernel_client import JupyterKernelBackend
from ..runtime_backend import RuntimeBackend
from .base import ProviderDiscoveryResult, RuntimeProvider


class LocalJupyterProvider(RuntimeProvider):
    provider_id: ClassVar[str] = "local_jupyter"

    def discover(self) -> ProviderDiscoveryResult:
        if importlib.util.find_spec("ipykernel") is None:
            return ProviderDiscoveryResult(
                available=False,
                reason="ipykernel is not installed; cannot launch a local kernel (pip install ipykernel).",
            )
        return ProviderDiscoveryResult(available=True, metadata={"kernel_name": self.config.get("kernel_name", "python3")})

    def _create_backend(self) -> RuntimeBackend:
        return JupyterKernelBackend(connection_file=None, kernel_name=self.config.get("kernel_name", "python3"))
