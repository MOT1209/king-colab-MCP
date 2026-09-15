import time

import pytest

from google_colab_mcp.jobs.job_manager import JobManager
from google_colab_mcp.jobs.models import JobStatus
from google_colab_mcp.utils.errors import JobNotFoundError


def _wait_for_terminal(manager, job_id, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = manager.get(job_id)
        if job.status.is_terminal:
            return job
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not reach a terminal state in time")


def test_successful_job_completes():
    manager = JobManager(max_concurrent_jobs=2)
    job = manager.submit("test", lambda j: 42)
    finished = _wait_for_terminal(manager, job.job_id)
    assert finished.status == JobStatus.COMPLETED
    assert finished.result == 42


def test_failing_job_is_marked_failed():
    def _boom(job):
        raise RuntimeError("kaboom")

    manager = JobManager(max_concurrent_jobs=2)
    job = manager.submit("test", _boom)
    finished = _wait_for_terminal(manager, job.job_id)
    assert finished.status == JobStatus.FAILED
    assert finished.error["message"] == "kaboom"


def test_timeout_job_is_marked_timeout():
    def _slow(job):
        time.sleep(2)
        return "done"

    manager = JobManager(max_concurrent_jobs=2)
    job = manager.submit("test", _slow, timeout_seconds=0.1)
    finished = _wait_for_terminal(manager, job.job_id, timeout=5)
    assert finished.status == JobStatus.TIMEOUT


def test_cancel_queued_job():
    manager = JobManager(max_concurrent_jobs=1)
    # occupy the only slot so the second job stays queued
    blocker = manager.submit("test", lambda j: time.sleep(0.3))
    queued = manager.submit("test", lambda j: 1)
    manager.cancel(queued.job_id)
    finished = _wait_for_terminal(manager, queued.job_id, timeout=5)
    assert finished.status == JobStatus.CANCELLED
    _wait_for_terminal(manager, blocker.job_id)


def test_get_unknown_job_raises():
    manager = JobManager()
    with pytest.raises(JobNotFoundError):
        manager.get("job_doesnotexist")


def test_get_logs_accumulate():
    manager = JobManager()
    job = manager.submit("test", lambda j: j.append_log("custom line") or 1)
    _wait_for_terminal(manager, job.job_id)
    logs = manager.get_logs(job.job_id)
    assert any("custom line" in line for line in logs)
    assert any("started" in line.lower() for line in logs)
