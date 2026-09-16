# Authentication

## What's implemented today

`security/auth.py::authenticate()` supports two modes, selected by
`COLAB_AUTH_MODE` (only checked when `REQUIRE_AUTH=true`):

- **`none`** (default): no MCP-level authentication. Every caller is the
  `anonymous` principal. Only appropriate for local/dev use.
- **`api_key`**: a static bearer token (`MCP_AUTH_TOKEN`), compared with
  `hmac.compare_digest` (constant-time, avoids timing side-channels).
  Missing or mismatched tokens raise `AuthenticationError`.

Both modes return a `Principal(id, auth_mode)` used for rate limiting and
audit logging.

## What's designed but not implemented

`COLAB_AUTH_MODE` also accepts `google_oauth` and `service_account`
values in configuration — **selecting either currently raises
`AuthenticationError` immediately.** They are not silently accepted or
faked as working. The `Principal`/`authenticate()` seam exists
specifically so these can be added later without touching any tool code:

```python
# security/auth.py, sketch of what a real OAuth mode would add:
def authenticate(settings: Settings, provided_token: str | None) -> Principal:
    ...
    if settings.colab_auth_mode == "google_oauth":
        claims = verify_google_id_token(provided_token, settings.google_oauth_client_id)
        return Principal(id=claims["sub"], auth_mode="google_oauth")
```

A real implementation would need, at minimum:

- Token verification against Google's public keys (e.g. via
  `google.oauth2.id_token.verify_oauth2_token`), not just JWT decoding.
- Token rotation/expiration handling — reject expired tokens rather than
  trusting `exp` blindly, and support refresh-token exchange for
  long-lived sessions.
- A `service_account` mode verifying a signed JWT against a configured
  service account's public key (e.g. Google's service account
  credentials flow), for non-interactive/CI use.

None of this is implemented in this release. If you need it, treat this
document as the spec for what to build, not as a description of existing
behavior.

## Per-session permissions (implemented)

Independent of principal-level authentication, a session created via
`colab_create_session` can carry a `permissions` list. If non-empty, any
tool call naming that `session_id` is checked against it
(`security/permissions.py::check_session_tool_permission`) — a
tool not in the list is rejected with `AuthorizationError`, regardless of
what the server-wide `ALLOWED_TOOLS`/`DENIED_TOOLS` say. This lets an
agent hand a narrowly-scoped session (e.g. `["colab_get_cpu",
"colab_get_gpu"]`) to a less-trusted sub-task.

## Secrets

No credentials are ever hard-coded in source. Everything comes from
environment variables (`.env.example`); `MCP_AUTH_TOKEN` and any future
OAuth client secrets follow the same pattern. `security/redact.py`
scrubs anything that *looks* like a credential out of error messages,
logs, and audit entries regardless of auth mode.
