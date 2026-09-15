"""Manages long-running, asynchronous tasks (training runs, batch executions).

Every MCP tool call must return promptly, so anything that can take longer
than a few seconds — training, long notebook runs — starts a job and returns
a job_id immediately. Callers then poll `get_job` / `get_logs`, or cancel.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable

from ..utils.errors import JobNotFoundError
from ..utils.ids import new_id
from .models import Job, JobStatus


class JobManager:
    def __init__(self, max_concurrent_jobs: int = 4):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(max_concurrent_jobs)

    def submit(
        self,
        kind: str,
        target: Callable[[Job], Any],
        timeout_seconds: float | None = None,
    ) -> Job:
        job = Job(job_id=new_id("job"), kind=kind)
        with self._lock:
            self._jobs[job.job_id] = job

        thread = threading.Thread(
            target=self._run,
            args=(job, target, timeout_seconds),
            daemon=True,
        )
        thread.start()
        return job

    def _run(self, job: Job, target: Callable[[Job], Any], timeout_seconds: float | None) -> None:
        acquired = self._semaphore.acquire(timeout=timeout_seconds or 3600)
        if not acquired:
            job.status = JobStatus.TIMEOUT
            job.append_log("Timed out waiting for a free execution slot.")
            job.finished_at = time.time()
            return

        if job.cancel_requested:
            job.status = JobStatus.CANCELLED
            job.append_log("Job was cancelled before it started.")
            job.finished_at = time.time()
            self._semaphore.release()
            return

        result_holder: dict[str, Any] = {}
        error_holder: dict[str, Any] = {}

        def _target_wrapper():
            try:
                job.status = JobStatus.RUNNING
                job.started_at = time.time()
                job.append_log(f"Job {job.job_id} started.")
                result_holder["value"] = target(job)
            except Exception as exc:  # noqa: BLE001
                error_holder["value"] = {"type": type(exc).__name__, "message": str(exc)}

        job.status = JobStatus.STARTING
        worker = threading.Thread(target=_target_wrapper, daemon=True)
        worker.start()
        worker.join(timeout=timeout_seconds)

        try:
            if worker.is_alive():
                job.status = JobStatus.TIMEOUT
                job.append_log(f"Job exceeded timeout of {timeout_seconds}s; marked as timed out.")
            elif job.cancel_requested:
                job.status = JobStatus.CANCELLED
                job.append_log("Job was cancelled.")
            elif "value" in error_holder:
                job.status = JobStatus.FAILED
                job.error = error_holder["value"]
                job.append_log(f"Job failed: {job.error}")
            else:
                job.status = JobStatus.COMPLETED
                job.result = result_holder.get("value")
                job.progress = 1.0
                job.append_log("Job completed successfully.")
        finally:
            job.finished_at = time.time()
            self._semaphore.release()

    def get(self, job_id: str) -> Job:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise JobNotFoundError(f"No such job: {job_id}")
        return job

    def cancel(self, job_id: str) -> Job:
        job = self.get(job_id)
        if job.status.is_terminal:
            return job
        job.cancel_requested = True
        job.append_log("Cancellation requested.")
        # Cooperative cancellation: a queued job is caught by the cancel_requested
        # check in _run() before it starts. A job whose target is already running
        # must itself poll job.cancel_requested (or be interrupted via its runtime
        # session, as colab_stop_training does) to stop early; otherwise it runs
        # to completion and this flag is only advisory.
        return job

    def list_jobs(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def get_logs(self, job_id: str) -> list[str]:
        return self.get(job_id).logs
