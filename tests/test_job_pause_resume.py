import time

from google_colab_mcp.jobs.job_manager import JobManager
from google_colab_mcp.jobs.models import JobStatus


def test_pause_marks_running_job_paused():
    manager = JobManager(max_concurrent_jobs=2)

    def _long_running(job):
        time.sleep(0.3)
        return "done"

    job = manager.submit("test", _long_running, timeout_seconds=5)
    time.sleep(0.05)  # let it reach RUNNING
    paused = manager.pause(job.job_id)
    assert paused.status == JobStatus.PAUSED
    assert paused.pause_requested is True

    resumed = manager.resume(job.job_id)
    assert resumed.status == JobStatus.RUNNING
    assert resumed.pause_requested is False


def test_pause_on_terminal_job_is_noop():
    manager = JobManager()
    job = manager.submit("test", lambda j: 1)
    deadline = time.time() + 3
    while time.time() < deadline and not job.status.is_terminal:
        time.sleep(0.02)
    result = manager.pause(job.job_id)
    assert result.status == JobStatus.COMPLETED


def test_job_records_session_and_runtime_id():
    manager = JobManager()

    def _target(job):
        job.session_id = "sess_x"
        job.runtime_id = "rt_x"
        job.record_metric("loss", 0.5, step=1)
        return "ok"

    job = manager.submit("test", _target)
    deadline = time.time() + 3
    while time.time() < deadline and not job.status.is_terminal:
        time.sleep(0.02)
    data = job.to_dict()
    assert data["session_id"] == "sess_x"
    assert data["runtime_id"] == "rt_x"
    assert data["metrics"]["loss"][0]["value"] == 0.5
