"""Runs code against a session's runtime backend and normalizes the result."""
from __future__ import annotations

from typing import Any

from ..utils.errors import ExecutionError
from .session_manager import SessionManager


class ExecutionManager:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def run(self, code: str, session_id: str | None, timeout: float) -> dict[str, Any]:
        session = (
            self.session_manager.get(session_id)
            if session_id
            else self.session_manager.get_or_create_default()
        )
        result = session.backend.execute(code, timeout=timeout)

        if result.error:
            raise ExecutionError(
                f"{result.error.get('ename')}: {result.error.get('evalue')}",
                details="\n".join(result.error.get("traceback", [])),
            )

        return {
            "session_id": session.session_id,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "result": result.result_repr,
            "display_data": result.display_data,
            "execution_count": result.execution_count,
        }
