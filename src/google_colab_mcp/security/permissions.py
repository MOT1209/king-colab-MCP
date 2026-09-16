"""Per-tool allow/deny list enforcement (server-wide) and per-session tool
permission enforcement (finer-grained: a specific session can be scoped to
only the tools it was created for)."""
from __future__ import annotations

from typing import Any

from ..config import Settings
from ..utils.errors import AuthorizationError


def check_tool_permission(settings: Settings, tool_name: str) -> None:
    if settings.denied_tools and tool_name in settings.denied_tools:
        raise AuthorizationError(f"Tool '{tool_name}' is explicitly denied by DENIED_TOOLS.")
    if settings.allowed_tools and tool_name not in settings.allowed_tools:
        raise AuthorizationError(
            f"Tool '{tool_name}' is not in the ALLOWED_TOOLS allowlist.",
            suggestion="Add it to ALLOWED_TOOLS or leave ALLOWED_TOOLS empty to allow all tools.",
        )


def check_session_tool_permission(session_manager: Any, tool_name: str, session_id: str | None) -> None:
    """If a call targets a specific session and that session was created
    with a non-empty `permissions` list, the tool must be in that list.
    A session with no permissions list set is unrestricted (server-wide
    ALLOWED_TOOLS/DENIED_TOOLS still apply)."""
    if not session_id:
        return
    try:
        session = session_manager.get(session_id)
    except Exception:
        return  # let the tool handler itself raise a clear "no such session" error
    if session.permissions and tool_name not in session.permissions:
        raise AuthorizationError(
            f"Tool '{tool_name}' is not permitted for session '{session_id}' "
            f"(session permissions: {session.permissions}).",
            suggestion="Create a session with this tool included in its 'permissions' list.",
        )
