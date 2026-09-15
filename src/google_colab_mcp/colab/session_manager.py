"""Tracks named runtime sessions (one Colab/Jupyter kernel connection each)."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable

from ..utils.errors import RuntimeUnavailableError
from ..utils.ids import new_id
from .kernel_client import JupyterKernelBackend
from .runtime_backend import RuntimeBackend


@dataclass
class SessionInfo:
    session_id: str
    backend: RuntimeBackend
    connection_file: str | None
    created_at: float
    label: str = "default"


class SessionManager:
    def __init__(self, backend_factory: Callable[[str | None], RuntimeBackend] | None = None):
        self._sessions: dict[str, SessionInfo] = {}
        self._lock = threading.Lock()
        self._backend_factory = backend_factory or (lambda cf: JupyterKernelBackend(connection_file=cf))

    def create_session(self, connection_file: str | None = None, label: str = "default") -> SessionInfo:
        import time

        backend = self._backend_factory(connection_file)
        backend.connect()
        session = SessionInfo(
            session_id=new_id("sess"),
            backend=backend,
            connection_file=connection_file,
            created_at=time.time(),
            label=label,
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
        return self.create_session(label="default")

    def list_sessions(self) -> list[SessionInfo]:
        with self._lock:
            return list(self._sessions.values())

    def close_session(self, session_id: str) -> None:
        session = self.get(session_id)
        session.backend.disconnect()
        with self._lock:
            self._sessions.pop(session_id, None)

    def close_all(self) -> None:
        for session_id in list(self._sessions.keys()):
            try:
                self.close_session(session_id)
            except Exception:
                pass
