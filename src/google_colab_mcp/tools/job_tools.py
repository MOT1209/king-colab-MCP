from __future__ import annotations

from typing import Any

from ..context import ServerContext
from .registry import ToolRegistry, ToolSpec


def _get_job(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.job_manager.get(args["job_id"]).to_dict(include_logs=args.get("include_logs", False))


def _cancel_job(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.job_manager.cancel(args["job_id"]).to_dict()


def _get_logs(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    logs = ctx.job_manager.get_logs(args["job_id"])
    tail = args.get("tail")
    if tail:
        logs = logs[-tail:]
    return {"job_id": args["job_id"], "logs": logs}


def _list_jobs(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    jobs = ctx.job_manager.list_jobs()
    status_filter = args.get("status")
    if status_filter:
        jobs = [j for j in jobs if j.status.value == status_filter]
    return {"jobs": [j.to_dict() for j in jobs], "count": len(jobs)}


def _pause_job(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.job_manager.pause(args["job_id"]).to_dict()


def _resume_job(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.job_manager.resume(args["job_id"]).to_dict()


def _get_artifacts(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    job_id = args.get("job_id")
    if job_id:
        return {"job_id": job_id, "artifacts": ctx.artifact_manager.list_for_job(job_id)}
    return {"artifacts_by_job": ctx.artifact_manager.list_all()}


def register(registry: ToolRegistry) -> None:
    registry.register(ToolSpec(
        name="colab_get_job",
        description="Get the status, progress, and result of a job (e.g. a training run) by job_id.",
        input_schema={
            "type": "object",
            "properties": {"job_id": {"type": "string"}, "include_logs": {"type": "boolean", "default": False}},
            "required": ["job_id"],
        },
        handler=_get_job,
    ))
    registry.register(ToolSpec(
        name="colab_cancel_job",
        description="Request cancellation of a running or queued job.",
        input_schema={"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]},
        handler=_cancel_job,
    ))
    registry.register(ToolSpec(
        name="colab_get_logs",
        description="Get a job's accumulated log lines, optionally only the last N.",
        input_schema={
            "type": "object",
            "properties": {"job_id": {"type": "string"}, "tail": {"type": "integer"}},
            "required": ["job_id"],
        },
        handler=_get_logs,
    ))
    registry.register(ToolSpec(
        name="colab_list_jobs",
        description="List all known jobs, optionally filtered by status (queued/starting/running/completed/failed/cancelled/timeout).",
        input_schema={"type": "object", "properties": {"status": {"type": "string"}}},
        handler=_list_jobs,
    ))
    registry.register(ToolSpec(
        name="colab_pause_job",
        description="Cooperatively request a running job to pause. The job's own code must poll for this to actually stop work.",
        input_schema={"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]},
        handler=_pause_job,
    ))
    registry.register(ToolSpec(
        name="colab_resume_job",
        description="Resume a paused job.",
        input_schema={"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]},
        handler=_resume_job,
    ))
    registry.register(ToolSpec(
        name="colab_get_artifacts",
        description="List artifacts (models, datasets, logs, metrics, reports) produced by a job, or all jobs if job_id is omitted.",
        input_schema={"type": "object", "properties": {"job_id": {"type": "string"}}},
        handler=_get_artifacts,
    ))
