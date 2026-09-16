from __future__ import annotations

from typing import Any

from ..context import ServerContext
from .registry import ToolRegistry, ToolSpec

_PROVIDER_IDS = ["colab", "local_jupyter", "remote_jupyter", "docker"]


def _create_session(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    session = ctx.session_manager.create_session(
        provider_id=args.get("provider", "local_jupyter"),
        provider_config=args.get("provider_config"),
        label=args.get("label", "default"),
        owner=args.get("owner", "anonymous"),
        permissions=args.get("permissions"),
    )
    return session.to_dict()


def _get_session(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.session_manager.get(args["session_id"]).to_dict()


def _list_sessions(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    sessions = [s.to_dict() for s in ctx.session_manager.list_sessions()]
    return {"sessions": sessions, "count": len(sessions)}


def _reconnect_session(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    session = ctx.session_manager.reconnect(args["session_id"])
    return session.to_dict()


def _close_session(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    ctx.session_manager.close_session(args["session_id"])
    return {"session_id": args["session_id"], "closed": True}


def _health_check(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.session_manager.health_check(args["session_id"])


def _get_runtime(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    session_id = args.get("session_id")
    sessions = ctx.session_manager.list_sessions()
    info = ctx.runtime_manager.get_runtime_info(session_id)
    return {"active_sessions": [s.to_dict() for s in sessions], **info}


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
        description=(
            "Open a new runtime session against a specific RuntimeProvider: 'colab' (a real, "
            "verified Google Colab kernel — requires provider_config.connection_file and will "
            "refuse to pretend a non-Colab kernel is Colab), 'local_jupyter' (a kernel this "
            "server launches itself, default), 'remote_jupyter' (any other Jupyter kernel via "
            "a connection file), or 'docker' (a fresh containerized kernel)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "provider": {"type": "string", "enum": _PROVIDER_IDS, "default": "local_jupyter"},
                "provider_config": {
                    "type": "object",
                    "description": "Provider-specific config, e.g. {\"connection_file\": \"...\"} for colab/remote_jupyter, {\"image\": \"...\"} for docker.",
                },
                "label": {"type": "string", "default": "default"},
                "owner": {"type": "string"},
                "permissions": {"type": "array", "items": {"type": "string"}},
            },
        },
        handler=_create_session,
    ))
    registry.register(ToolSpec(
        name="colab_get_session",
        description="Get one session's status, provider, owner, and permissions.",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}, "required": ["session_id"]},
        handler=_get_session,
    ))
    registry.register(ToolSpec(
        name="colab_list_sessions",
        description="List all runtime sessions and their status.",
        input_schema={"type": "object", "properties": {}},
        handler=_list_sessions,
    ))
    registry.register(ToolSpec(
        name="colab_reconnect_session",
        description="Force a reconnect attempt for a session using its original provider/config.",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}, "required": ["session_id"]},
        handler=_reconnect_session,
    ))
    registry.register(ToolSpec(
        name="colab_close_session",
        description="Disconnect and remove a session (and, for provider='docker', tear down its container).",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}, "required": ["session_id"]},
        handler=_close_session,
    ))
    registry.register(ToolSpec(
        name="colab_session_health",
        description="Run a health check on a session's provider/backend without waiting for the background monitor.",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}, "required": ["session_id"]},
        handler=_health_check,
    ))
    registry.register(ToolSpec(
        name="colab_get_runtime",
        description="Get overall runtime status: active sessions, Python version, CUDA/torch availability.",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}},
        handler=_get_runtime,
    ))
    registry.register(ToolSpec(
        name="colab_get_gpu",
        description="Get GPU/VRAM info for a runtime session (device name, memory, count), probed via multiple detection methods.",
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
