from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

    @property
    def is_terminal(self) -> bool:
        return self in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMEOUT)


@dataclass
class Job:
    job_id: str
    kind: str
    session_id: str | None = None
    runtime_id: str | None = None
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    logs: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: dict[str, Any] | None = None
    cancel_requested: bool = False
    pause_requested: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def append_log(self, line: str) -> None:
        with self._lock:
            self.logs.append(f"[{time.strftime('%H:%M:%S')}] {line}")

    def record_metric(self, name: str, value: Any, step: int | None = None) -> None:
        """Append a structured metric point (e.g. {"step": 10, "value": 0.42})
        instead of relying on callers to grep free-text log lines for numbers."""
        with self._lock:
            series = self.metrics.setdefault(name, [])
            series.append({"value": value, "step": step, "ts": time.time()})

    def to_dict(self, include_logs: bool = False) -> dict[str, Any]:
        with self._lock:
            data = {
                "job_id": self.job_id,
                "kind": self.kind,
                "session_id": self.session_id,
                "runtime_id": self.runtime_id,
                "status": self.status.value,
                "progress": self.progress,
                "created_at": self.created_at,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "metrics": self.metrics,
                "result": self.result,
                "error": self.error,
            }
            if include_logs:
                data["logs"] = list(self.logs)
            return data
