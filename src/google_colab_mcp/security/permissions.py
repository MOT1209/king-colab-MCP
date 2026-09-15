"""Per-tool allow/deny list enforcement."""
from __future__ import annotations

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
