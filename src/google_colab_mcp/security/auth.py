"""Authentication abstraction.

This module intentionally defines a small `Principal` + `authenticate()`
seam rather than a concrete auth backend, so additional modes (Google OAuth,
service accounts, custom SSO) can be added later without touching tool code.
No credentials are ever hard-coded here; everything comes from environment
variables via `Settings`.
"""
from __future__ import annotations

import hmac
from dataclasses import dataclass

from ..config import Settings
from ..utils.errors import AuthenticationError


@dataclass(frozen=True)
class Principal:
    id: str
    auth_mode: str


def authenticate(settings: Settings, provided_token: str | None) -> Principal:
    """Validate the caller's credentials and return a Principal.

    Modes:
      - "none": no auth required, every caller is the anonymous principal
        (only safe for local/dev use — REQUIRE_AUTH should be false).
      - "api_key": a static bearer token (MCP_AUTH_TOKEN) must be supplied
        and match exactly (constant-time compare).

    Additional modes (google_oauth, service_account) are reserved for future
    implementations and currently raise AuthenticationError if selected
    without a corresponding provided_token validator being wired in.
    """
    if not settings.require_auth:
        return Principal(id="anonymous", auth_mode="none")

    if settings.colab_auth_mode == "api_key":
        if not settings.mcp_auth_token:
            raise AuthenticationError(
                "Server is configured to require auth but MCP_AUTH_TOKEN is unset.",
                suggestion="Set MCP_AUTH_TOKEN in the environment.",
            )
        if not provided_token or not hmac.compare_digest(provided_token, settings.mcp_auth_token):
            raise AuthenticationError("Invalid or missing MCP auth token.")
        return Principal(id="api_key_user", auth_mode="api_key")

    raise AuthenticationError(
        f"Unsupported COLAB_AUTH_MODE '{settings.colab_auth_mode}' with REQUIRE_AUTH enabled.",
        suggestion="Use COLAB_AUTH_MODE=api_key with MCP_AUTH_TOKEN set, or disable REQUIRE_AUTH.",
    )
