from __future__ import annotations

from typing import Any

from ..context import ServerContext
from ..utils.errors import ValidationError
from .registry import ToolRegistry, ToolSpec


def _execute_code(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    code = args["code"]
    if len(code) > ctx.settings.max_code_length:
        raise ValidationError(
            f"Code length {len(code)} exceeds MAX_CODE_LENGTH ({ctx.settings.max_code_length}).",
        )
    timeout = args.get("timeout_seconds", ctx.settings.colab_timeout)
    return ctx.execution_manager.run(code, args.get("session_id"), timeout)


def _interrupt_execution(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    session = (
        ctx.session_manager.get(args["session_id"])
        if args.get("session_id")
        else ctx.session_manager.get_or_create_default()
    )
    session.backend.interrupt()
    return {"session_id": session.session_id, "interrupted": True}


def register(registry: ToolRegistry) -> None:
    registry.register(ToolSpec(
        name="colab_execute_code",
        description=(
            "Execute a snippet of Python code in a Colab/Jupyter runtime session and return "
            "stdout, stderr, the last expression's repr, and any rich display data."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python source to execute."},
                "session_id": {"type": "string", "description": "Existing session to run in; omit to use/create the default session."},
                "timeout_seconds": {"type": "number", "description": "Max seconds to wait for execution to finish."},
            },
            "required": ["code"],
        },
        handler=_execute_code,
    ))
    registry.register(ToolSpec(
        name="colab_stop_execution",
        description="Interrupt whatever is currently executing in a runtime session (like a keyboard interrupt).",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}},
        handler=_interrupt_execution,
    ))
