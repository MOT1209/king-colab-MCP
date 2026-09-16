"""Tracks named runtime sessions, each backed by a `RuntimeProvider`.

    MCP Tool → SessionManager → RuntimeProvider → RuntimeBackend

Sessions carry ownership/permission metadata (section 5 of the runtime
spec) and their status is always read from the owning provider's lifecycle
state (`RuntimeState`), never a bare connected/disconnected flag.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from ..utils.errors import RuntimeUnavailableError, ValidationError
from ..utils.ids import new_id
from .providers import PROVIDER_REGISTRY, RuntimeProvider, RuntimeState
from .runtime_backend import RuntimeBackend


@dataclass
class SessionInfo:
    session_id: str
    runtime_id: str
    provider: RuntimeProvider
    backend: RuntimeBackend
    created_at: float
    label: str = "default"
    owner: str = "anonymous"
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    last_activity: float = field(default_factory=time.time)

    @property
    def provider_id(self) -> str:
        return self.provider.provider_id

    @property
    def status(self) -> str:
        return self.provider.state.value

    def touch(self) -> None:
        self.last_activity = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "runtime_id": self.runtime_id,
            "provider": self.provider_id,
            "label": self.label,
            "status": self.status,
            "connected": self.backend.is_connected,
            "owner": self.owner,
            "permissions": self.permissions,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "metadata": self.metadata,
        }


class SessionManager:
    def __init__(self, provider_registry: dict[str, type[RuntimeProvider]] | None = None):
        self._sessions: dict[str, SessionInfo] = {}
        self._lock = threading.Lock()
        self._provider_registry = provider_registry or PROVIDER_REGISTRY

    def _build_provider(self, provider_id: str, provider_config: dict[str, Any] | None) -> RuntimeProvider:
        provider_cls = self._provider_registry.get(provider_id)
        if provider_cls is None:
            raise ValidationError(
                f"Unknown runtime provider: {provider_id!r}",
                suggestion=f"Use one of: {sorted(self._provider_registry.keys())}",
            )
        return provider_cls(provider_config or {})

    def create_session(
        self,
        provider_id: str = "local_jupyter",
        provider_config: dict[str, Any] | None = None,
        label: str = "default",
        owner: str = "anonymous",
        permissions: list[str] | None = None,
    ) -> SessionInfo:
        provider = self._build_provider(provider_id, provider_config)
        backend = provider.connect()
        session = SessionInfo(
            session_id=new_id("sess"),
            runtime_id=new_id("rt"),
            provider=provider,
            backend=backend,
            created_at=time.time(),
            label=label,
            owner=owner,
            permissions=permissions or [],
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> SessionInfo:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise RuntimeUnavailableError(f"No such session: {session_id}")
        return session

    def get_or_create_default(self) -> SessionInfo:
        with self._lock:
            for session in self._sessions.values():
                if session.label == "default" and session.backend.is_connected:
                    return session
        return self.create_session(provider_id="local_jupyter", label="default")

    def list_sessions(self) -> list[SessionInfo]:
        with self._lock:
            return list(self._sessions.values())

    def reconnect(self, session_id: str) -> SessionInfo:
        session = self.get(session_id)
        session.provider.state = RuntimeState.RECONNECTING
        new_backend = session.provider.connect()
        session.backend = new_backend
        session.touch()
        return session

    def health_check(self, session_id: str) -> dict[str, Any]:
        session = self.get(session_id)
        return session.provider.health_check(session.backend)

    def close_session(self, session_id: str) -> None:
        session = self.get(session_id)
        session.provider.disconnect(session.backend)
        with self._lock:
            self._sessions.pop(session_id, None)

    def close_all(self) -> None:
        for session_id in list(self._sessions.keys()):
            try:
                self.close_session(session_id)
            except Exception:
                pass
