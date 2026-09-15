"""ML training/evaluation workflows, layered entirely on top of
`colab_execute_code` + the job manager. No specific ML framework is
required or imported by the server itself — whatever the submitted code
imports (PyTorch, TensorFlow, Transformers, scikit-learn, XGBoost, ...) is
resolved inside the runtime, not here.
"""
from __future__ import annotations

from typing import Any

from ..context import ServerContext
from ..jobs.models import Job
from .registry import ToolRegistry, ToolSpec


def _run_training(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    code = args["code"]
    session_id = args.get("session_id")
    timeout = args.get("timeout_seconds", 3600)

    def _target(job: Job) -> dict[str, Any]:
        session = ctx.session_manager.get(session_id) if session_id else ctx.session_manager.get_or_create_default()
        job.metadata["session_id"] = session.session_id
        job.append_log(f"Running training code in session {session.session_id}.")
        result = ctx.execution_manager.run(code, session.session_id, timeout=timeout)
        for line in result["stdout"].splitlines():
            job.append_log(line)
        job.progress = 1.0
        return result

    job = ctx.job_manager.submit(kind="training", target=_target, timeout_seconds=timeout)
    return {"job_id": job.job_id, "status": job.status.value}


def _stop_training(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    job = ctx.job_manager.get(args["job_id"])
    session_id = job.metadata.get("session_id")
    if session_id:
        try:
            session = ctx.session_manager.get(session_id)
            session.backend.interrupt()
        except Exception:
            pass
    return ctx.job_manager.cancel(job.job_id).to_dict()


def _evaluate_model(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    timeout = args.get("timeout_seconds", ctx.settings.colab_timeout)
    return ctx.execution_manager.run(args["code"], args.get("session_id"), timeout)


def _save_model(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    timeout = args.get("timeout_seconds", ctx.settings.colab_timeout)
    result = ctx.execution_manager.run(args["code"], args.get("session_id"), timeout)
    if args.get("job_id"):
        ctx.artifact_manager.register(args["job_id"], args.get("name", "model"), "model", args["artifact_path"])
    return result


def _export_model(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    timeout = args.get("timeout_seconds", ctx.settings.colab_timeout)
    result = ctx.execution_manager.run(args["code"], args.get("session_id"), timeout)
    if args.get("job_id"):
        ctx.artifact_manager.register(args["job_id"], args.get("name", "exported_model"), "model", args["artifact_path"])
    return result


def register(registry: ToolRegistry) -> None:
    registry.register(ToolSpec(
        name="colab_run_training",
        description=(
            "Start a training run as a background job: submits Python training code "
            "(any framework) to a runtime session and returns a job_id immediately. "
            "Poll with colab_get_job / colab_get_logs."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Full training script to execute."},
                "session_id": {"type": "string"},
                "timeout_seconds": {"type": "number", "default": 3600},
            },
            "required": ["code"],
        },
        handler=_run_training,
    ))
    registry.register(ToolSpec(
        name="colab_stop_training",
        description="Interrupt a running training job and mark it cancelled.",
        input_schema={"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]},
        handler=_stop_training,
    ))
    registry.register(ToolSpec(
        name="colab_evaluate_model",
        description="Run evaluation code synchronously against a runtime session and return its output.",
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "session_id": {"type": "string"},
                "timeout_seconds": {"type": "number"},
            },
            "required": ["code"],
        },
        handler=_evaluate_model,
    ))
    registry.register(ToolSpec(
        name="colab_save_model",
        description=(
            "Run model-saving code in a runtime session, then (optionally) register the "
            "resulting file under a job's artifacts via colab_get_artifacts."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "session_id": {"type": "string"},
                "timeout_seconds": {"type": "number"},
                "job_id": {"type": "string"},
                "name": {"type": "string"},
                "artifact_path": {"type": "string", "description": "Path (relative to the artifact root) the code saved to."},
            },
            "required": ["code"],
        },
        handler=_save_model,
    ))
    registry.register(ToolSpec(
        name="colab_export_model",
        description="Run model-export code (e.g. ONNX/TorchScript) in a runtime session and register the exported artifact.",
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "session_id": {"type": "string"},
                "timeout_seconds": {"type": "number"},
                "job_id": {"type": "string"},
                "name": {"type": "string"},
                "artifact_path": {"type": "string"},
            },
            "required": ["code"],
        },
        handler=_export_model,
    ))
