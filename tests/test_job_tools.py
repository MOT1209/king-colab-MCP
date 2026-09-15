from google_colab_mcp.tools.job_tools import register as register_job_tools
from google_colab_mcp.tools.registry import ToolRegistry


def _registry():
    registry = ToolRegistry()
    register_job_tools(registry)
    return registry


def test_get_job_and_logs_and_cancel(ctx):
    registry = _registry()
    job = ctx.job_manager.submit("test", lambda j: (j.append_log("working"), 1)[1])
    import time

    deadline = time.time() + 3
    while time.time() < deadline and not job.status.is_terminal:
        time.sleep(0.02)

    result = registry.get("colab_get_job").handler(ctx, {"job_id": job.job_id, "include_logs": True})
    assert result["status"] == "completed"
    assert "logs" in result

    logs = registry.get("colab_get_logs").handler(ctx, {"job_id": job.job_id})
    assert any("working" in line for line in logs["logs"])

    listed = registry.get("colab_list_jobs").handler(ctx, {})
    assert listed["count"] >= 1


def test_get_artifacts_for_job_and_all(ctx):
    registry = _registry()
    ctx.artifact_manager.path_guard.root.joinpath("out.txt").write_text("x")
    ctx.artifact_manager.register("job_x", "out", "log", "out.txt")

    for_job = registry.get("colab_get_artifacts").handler(ctx, {"job_id": "job_x"})
    assert for_job["job_id"] == "job_x"
    assert len(for_job["artifacts"]) == 1

    all_artifacts = registry.get("colab_get_artifacts").handler(ctx, {})
    assert "job_x" in all_artifacts["artifacts_by_job"]
