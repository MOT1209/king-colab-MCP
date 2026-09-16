"""Runs code against a session's runtime backend and normalizes the result."""
from __future__ import annotations

from typing import Any

from ..utils.errors import ExecutionError
from .session_manager import SessionManager

_DEFAULT_MAX_OUTPUT_BYTES = 2_000_000


def _truncate(text: str, max_bytes: int) -> tuple[str, bool]:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text, False
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + f"\n... [truncated, {len(encoded) - max_bytes} bytes omitted]", True


class ExecutionManager:
    def __init__(self, session_manager: SessionManager, max_output_bytes: int = _DEFAULT_MAX_OUTPUT_BYTES):
        self.session_manager = session_manager
        self.max_output_bytes = max_output_bytes

    def run(self, code: str, session_id: str | None, timeout: float) -> dict[str, Any]:
        session = (
            self.session_manager.get(session_id)
            if session_id
            else self.session_manager.get_or_create_default()
        )
        session.touch()
        result = session.backend.execute(code, timeout=timeout)

        if result.error:
            raise ExecutionError(
                f"{result.error.get('ename')}: {result.error.get('evalue')}",
                details="\n".join(result.error.get("traceback", [])),
            )

        stdout, stdout_truncated = _truncate(result.stdout, self.max_output_bytes)
        stderr, stderr_truncated = _truncate(result.stderr, self.max_output_bytes)

        return {
            "session_id": session.session_id,
            "stdout": stdout,
            "stderr": stderr,
            "output_truncated": stdout_truncated or stderr_truncated,
            "result": result.result_repr,
            "display_data": result.display_data,
            "execution_count": result.execution_count,
        }
