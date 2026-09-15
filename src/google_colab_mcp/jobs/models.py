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
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    logs: list[str] = field(default_factory=list)
    result: Any = None
    error: dict[str, Any] | None = None
    cancel_requested: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def append_log(self, line: str) -> None:
        with self._lock:
            self.logs.append(f"[{time.strftime('%H:%M:%S')}] {line}")

    def to_dict(self, include_logs: bool = False) -> dict[str, Any]:
        with self._lock:
            data = {
                "job_id": self.job_id,
                "kind": self.kind,
                "status": self.status.value,
                "progress": self.progress,
                "created_at": self.created_at,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "result": self.result,
                "error": self.error,
            }
            if include_logs:
                data["logs"] = list(self.logs)
            return data
