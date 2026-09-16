"""Cross-cutting request handling shared by every transport: auth, permission
checks, rate limiting, audit logging, and structured error formatting.

Kept independent of any specific MCP SDK transport so the same dispatch
logic could be reused if the transport layer changes.
"""
from __future__ import annotations

from typing import Any

from ..context import ServerContext
from ..logging.setup import get_logger
from ..security.auth import authenticate
from ..security.dangerous_tools import check_dangerous_tool_confirmed
from ..security.permissions import check_session_tool_permission, check_tool_permission
from ..security.redact import redact_secrets
from ..utils.errors import ColabMCPError
from ..utils.ids import new_id
from ..tools.registry import ToolRegistry

logger = get_logger("protocol")


def dispatch_tool_call(
    ctx: ServerContext,
    registry: ToolRegistry,
    tool_name: str,
    arguments: dict[str, Any] | None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Run one tool call through the full security/observability pipeline and
    return a JSON-able dict — either the tool's own result, or a structured
    `{"success": false, "error": {...}}` payload. Never raises."""
    request_id = new_id("req")
    arguments = arguments or {}

    try:
        principal = authenticate(ctx.settings, auth_token)
        ctx.rate_limiter.check(principal.id)
        check_tool_permission(ctx.settings, tool_name)
        check_dangerous_tool_confirmed(ctx.settings, tool_name, arguments)
        check_session_tool_permission(ctx.session_manager, tool_name, arguments.get("session_id"))

        spec = registry.get(tool_name)
        result = spec.handler(ctx, arguments)

        ctx.audit_logger.record(
            request_id=request_id, principal=principal.id, tool=tool_name,
            arguments=arguments, success=True,
        )
        logger.info("tool_call_succeeded", extra={"request_id": request_id, "tool": tool_name})
        return {"success": True, "result": result}

    except KeyError as exc:
        logger.warning(f"unknown tool: {exc}", extra={"request_id": request_id, "tool": tool_name})
        return {
            "success": False,
            "error": {
                "type": "unknown_tool_error",
                "message": str(exc),
                "details": redact_secrets(str(exc)),
                "suggestion": "Call list_tools to see the available tool names.",
            },
        }
    except ColabMCPError as exc:
        ctx.audit_logger.record(
            request_id=request_id, principal="unknown", tool=tool_name,
            arguments=arguments, success=False, error_type=exc.error_type,
        )
        logger.error(f"tool_call_failed: {exc.message}", extra={"request_id": request_id, "tool": tool_name})
        payload = exc.to_dict()
        payload["error"]["message"] = redact_secrets(str(payload["error"]["message"]))
        payload["error"]["details"] = redact_secrets(str(payload["error"]["details"]))
        return payload
    except Exception as exc:  # noqa: BLE001 — last-resort safety net, never crash the server
        ctx.audit_logger.record(
            request_id=request_id, principal="unknown", tool=tool_name,
            arguments=arguments, success=False, error_type="internal_error",
        )
        logger.error(f"unhandled exception: {exc}", extra={"request_id": request_id, "tool": tool_name})
        return {
            "success": False,
            "error": {
                "type": "internal_error",
                "message": "An unexpected internal error occurred.",
                "details": redact_secrets(str(exc)),
                "suggestion": "Check server logs with this request_id for more detail.",
            },
            "request_id": request_id,
        }
