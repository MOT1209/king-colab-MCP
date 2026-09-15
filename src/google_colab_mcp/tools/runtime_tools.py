from __future__ import annotations

from typing import Any

from ..context import ServerContext
from .registry import ToolRegistry, ToolSpec


def _create_session(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    session = ctx.session_manager.create_session(
        connection_file=args.get("connection_file"), label=args.get("label", "default")
    )
    return {"session_id": session.session_id, "label": session.label, "connected": session.backend.is_connected}


def _get_runtime(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    session_id = args.get("session_id")
    sessions = ctx.session_manager.list_sessions()
    info = ctx.runtime_manager.get_runtime_info(session_id)
    return {
        "active_sessions": [
            {"session_id": s.session_id, "label": s.label, "connected": s.backend.is_connected}
            for s in sessions
        ],
        **info,
    }


def _get_gpu(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.runtime_manager.get_gpu_info(args.get("session_id"))


def _get_cpu(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.runtime_manager.get_cpu_info(args.get("session_id"))


def _get_memory(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.runtime_manager.get_memory_info(args.get("session_id"))


def _get_disk(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.runtime_manager.get_disk_info(args.get("session_id"))


def _restart_runtime(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    session = ctx.session_manager.get(args["session_id"]) if args.get("session_id") else ctx.session_manager.get_or_create_default()
    session.backend.restart()
    return {"session_id": session.session_id, "restarted": True}


def register(registry: ToolRegistry) -> None:
    registry.register(ToolSpec(
        name="colab_create_session",
        description="Open a new runtime session (a Colab/Jupyter kernel connection). Omit connection_file to launch a local kernel.",
        input_schema={
            "type": "object",
            "properties": {
                "connection_file": {"type": "string", "description": "Path to a Jupyter kernel connection file to attach to."},
                "label": {"type": "string", "default": "default"},
            },
        },
        handler=_create_session,
    ))
    registry.register(ToolSpec(
        name="colab_get_runtime",
        description="Get overall runtime status: active sessions, Python version, CUDA/torch availability.",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}},
        handler=_get_runtime,
    ))
    registry.register(ToolSpec(
        name="colab_get_gpu",
        description="Get GPU/VRAM info for a runtime session (device name, memory, count).",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}},
        handler=_get_gpu,
    ))
    registry.register(ToolSpec(
        name="colab_get_cpu",
        description="Get CPU core count and utilization for a runtime session.",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}},
        handler=_get_cpu,
    ))
    registry.register(ToolSpec(
        name="colab_get_memory",
        description="Get RAM total/available/used for a runtime session.",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}},
        handler=_get_memory,
    ))
    registry.register(ToolSpec(
        name="colab_get_disk",
        description="Get disk usage for a runtime session.",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}},
        handler=_get_disk,
    ))
    registry.register(ToolSpec(
        name="colab_restart_runtime",
        description="Restart a runtime session's kernel (clears all variables/state).",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}},
        handler=_restart_runtime,
    ))
