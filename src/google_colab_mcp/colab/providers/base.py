"""RuntimeProvider: the seam between MCP tools and a concrete execution backend.

    MCP Tool → Runtime Manager → Runtime Provider → Execution Backend (RuntimeBackend)

A provider owns everything specific to *how* a runtime is reached and
verified (Colab genuineness checks, Docker container lifecycle, a plain
kernel connection file, ...). Once connected, every provider hands back the
same `RuntimeBackend` interface (`colab/runtime_backend.py`), so execution,
notebook, file, and package tools never need to know which provider is
behind a session.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar

from ...utils.errors import ProviderError
from ..runtime_backend import RuntimeBackend


class RuntimeState(str, Enum):
    DISCOVERING = "discovering"
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    IDLE = "idle"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    RECONNECTING = "reconnecting"


@dataclass
class ProviderDiscoveryResult:
    """Cheap, side-effect-light check of whether a provider *could* work
    with its current config — before spending time actually connecting."""

    available: bool
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class RuntimeProvider(ABC):
    """Base class for every runtime provider (Colab, local Jupyter, remote
    Jupyter, Docker, ...). Subclasses implement `discover()` and
    `_create_backend()`; `connect()` drives the shared lifecycle around them.
    """

    provider_id: ClassVar[str]

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.state = RuntimeState.DISCONNECTED
        self.last_discovery: ProviderDiscoveryResult | None = None
        self.verification: dict[str, Any] = {}

    @abstractmethod
    def discover(self) -> ProviderDiscoveryResult:
        """Return whether this provider can plausibly connect right now,
        without opening a real kernel connection."""

    @abstractmethod
    def _create_backend(self) -> RuntimeBackend:
        """Build the (not-yet-connected) RuntimeBackend this provider uses."""

    def authenticate(self) -> None:
        """Provider-specific authentication step. No-op by default."""

    def _verify(self, backend: RuntimeBackend) -> None:
        """Provider-specific post-connect verification (e.g. confirming a
        connected kernel is genuinely running on Google Colab). No-op by
        default; subclasses populate `self.verification`."""

    def connect(self) -> RuntimeBackend:
        self.state = RuntimeState.DISCOVERING
        discovery = self.discover()
        self.last_discovery = discovery
        if not discovery.available:
            self.state = RuntimeState.FAILED
            raise ProviderError(
                f"'{self.provider_id}' provider is unavailable: {discovery.reason}",
                details=str(discovery.metadata),
            )

        self.state = RuntimeState.CONNECTING
        try:
            self.state = RuntimeState.AUTHENTICATING
            self.authenticate()

            self.state = RuntimeState.INITIALIZING
            backend = self._create_backend()
            backend.connect()

            self._verify(backend)
        except ProviderError:
            self.state = RuntimeState.FAILED
            raise
        except Exception as exc:  # noqa: BLE001
            self.state = RuntimeState.FAILED
            raise ProviderError(
                f"'{self.provider_id}' provider failed to connect.", details=str(exc)
            ) from exc

        self.state = RuntimeState.READY
        return backend

    def health_check(self, backend: RuntimeBackend | None) -> dict[str, Any]:
        healthy = bool(backend and backend.is_connected)
        return {
            "provider": self.provider_id,
            "state": self.state.value,
            "healthy": healthy,
            "verification": self.verification,
        }

    def disconnect(self, backend: RuntimeBackend | None) -> None:
        if backend is not None:
            backend.disconnect()
        self.state = RuntimeState.DISCONNECTED
