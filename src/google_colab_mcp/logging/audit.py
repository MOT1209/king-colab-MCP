"""Append-only audit log for every tool invocation.

Every entry is redacted before being written and includes enough
correlation data (request_id, principal, tool, arguments summary, outcome)
to reconstruct "who did what, when" without ever persisting secrets.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

from ..security.redact import redact_secrets


class AuditLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(
        self,
        *,
        request_id: str,
        principal: str,
        tool: str,
        arguments: dict[str, Any],
        success: bool,
        error_type: str | None = None,
    ) -> None:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "request_id": request_id,
            "principal": principal,
            "tool": tool,
            "arguments": redact_secrets(json.dumps(arguments, default=str))[:4000],
            "success": success,
            "error_type": error_type,
        }
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
