"""Background health checks + automatic reconnect for runtime sessions.

Runs as a daemon thread that periodically calls
`SessionManager.health_check` for every session and, if a session has
dropped, attempts `SessionManager.reconnect` up to a bounded number of
times before giving up and leaving it `failed` for a human/agent to
investigate explicitly.
"""
from __future__ import annotations

import threading
import time

from ..logging.setup import get_logger
from .session_manager import SessionManager

logger = get_logger("health_monitor")


class HealthMonitor:
    def __init__(
        self,
        session_manager: SessionManager,
        interval_seconds: float = 30.0,
        max_reconnect_attempts: int = 3,
    ):
        self.session_manager = session_manager
        self.interval_seconds = interval_seconds
        self.max_reconnect_attempts = max_reconnect_attempts
        self._reconnect_attempts: dict[str, int] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def _run(self) -> None:
        while not self._stop_event.wait(self.interval_seconds):
            self.check_once()

    def check_once(self) -> None:
        for session in self.session_manager.list_sessions():
            try:
                health = self.session_manager.health_check(session.session_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"health_check failed for {session.session_id}: {exc}")
                continue

            if health["healthy"]:
                self._reconnect_attempts.pop(session.session_id, None)
                continue

            attempts = self._reconnect_attempts.get(session.session_id, 0)
            if attempts >= self.max_reconnect_attempts:
                continue

            self._reconnect_attempts[session.session_id] = attempts + 1
            logger.info(
                f"session {session.session_id} unhealthy, reconnect attempt "
                f"{attempts + 1}/{self.max_reconnect_attempts}"
            )
            try:
                self.session_manager.reconnect(session.session_id)
                logger.info(f"session {session.session_id} reconnect call succeeded")
                # Deliberately don't reset the attempt counter here: it only
                # resets once health_check() itself confirms healthy=true on
                # a later pass. A reconnect() call that returns without
                # raising is not proof the session is actually usable again
                # (e.g. a provider whose backend.connect() succeeds but the
                # kernel is still unresponsive) — resetting eagerly would let
                # such a session retry forever, defeating max_reconnect_attempts.
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"reconnect failed for {session.session_id}: {exc}")
