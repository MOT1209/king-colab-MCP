"""A Jupyter kernel launched inside a fresh Docker container.

Useful for fully isolated, disposable execution environments. Requires a
reachable Docker daemon and (today) Linux host networking — see
docs/RUNTIME_PROVIDERS.md for the known limitation on Docker Desktop.
"""
from __future__ import annotations

from typing import ClassVar

from ..docker_backend import DockerJupyterBackend, docker_available
from ..runtime_backend import RuntimeBackend
from .base import ProviderDiscoveryResult, RuntimeProvider


class DockerProvider(RuntimeProvider):
    provider_id: ClassVar[str] = "docker"

    def discover(self) -> ProviderDiscoveryResult:
        available, reason = docker_available()
        if not available:
            return ProviderDiscoveryResult(available=False, reason=reason)
        return ProviderDiscoveryResult(available=True, metadata={"image": self.config.get("image", "python:3.11-slim")})

    def _create_backend(self) -> RuntimeBackend:
        return DockerJupyterBackend(
            image=self.config.get("image", "python:3.11-slim"),
            install_ipykernel=self.config.get("install_ipykernel", True),
            startup_timeout=self.config.get("startup_timeout", 120),
        )
