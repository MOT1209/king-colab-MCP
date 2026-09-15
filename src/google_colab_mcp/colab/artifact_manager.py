"""Tracks artifacts (models, datasets, logs, metrics, reports) produced by jobs."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

from ..security.path_guard import PathGuard


class ArtifactManager:
    def __init__(self, path_guard: PathGuard):
        self.path_guard = path_guard
        self._lock = threading.Lock()
        self._index_path = self.path_guard.root / "_artifact_index.json"
        if not self._index_path.exists():
            self._write_index({})

    def _read_index(self) -> dict[str, list[dict[str, Any]]]:
        try:
            return json.loads(self._index_path.read_text())
        except Exception:
            return {}

    def _write_index(self, index: dict[str, Any]) -> None:
        self._index_path.write_text(json.dumps(index, indent=2))

    def register(self, job_id: str, name: str, artifact_type: str, relative_path: str) -> dict[str, Any]:
        resolved = self.path_guard.resolve(relative_path)
        entry = {
            "name": name,
            "type": artifact_type,
            "path": relative_path,
            "size_bytes": resolved.stat().st_size if resolved.exists() else 0,
            "registered_at": time.time(),
        }
        with self._lock:
            index = self._read_index()
            index.setdefault(job_id, []).append(entry)
            self._write_index(index)
        return entry

    def list_for_job(self, job_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return self._read_index().get(job_id, [])

    def list_all(self) -> dict[str, list[dict[str, Any]]]:
        with self._lock:
            return self._read_index()
