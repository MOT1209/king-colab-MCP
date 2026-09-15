# Security

This server executes arbitrary code on behalf of MCP clients, so security
is not optional. This document describes what is enforced today and how to
configure it.

## Threat model

The primary risk is a malicious or buggy MCP client/agent using this
server's tools to: read/exfiltrate secrets, escape the intended workspace
sandbox, exhaust resources (CPU/GPU/disk/requests), or execute
shell-injection payloads via package names or file paths.

## Controls

| Control | Where | What it does |
|---|---|---|
| Authentication | `security/auth.py` | `REQUIRE_AUTH=true` + `COLAB_AUTH_MODE=api_key` enforces a constant-time-compared bearer token (`MCP_AUTH_TOKEN`). The abstraction (`Principal`/`authenticate()`) is designed so Google OAuth or service-account modes can be added later without touching tool code. |
| Authorization | `security/permissions.py` | `ALLOWED_TOOLS` / `DENIED_TOOLS` env vars restrict which tools a deployment exposes. |
| Path sandboxing | `security/path_guard.py`, `colab/remote_fs.py` | Notebook/local file paths are resolved against `COLAB_WORKSPACE_ROOT` and rejected if they'd escape it (`PathAccessError`). Remote (in-runtime) file paths are confined to `COLAB_REMOTE_WORKSPACE_ROOT` the same way. |
| Rate limiting | `security/rate_limit.py` | Sliding-window limiter per principal, `MAX_REQUESTS_PER_MINUTE`. |
| Timeouts | every execution tool | `colab_execute_code`, notebook execution, and jobs all take `timeout_seconds` and enforce it; a hung kernel raises `ExecutionTimeoutError` instead of hanging the MCP call forever. |
| Secret redaction | `security/redact.py` | Applied to every tool error, log line, and audit entry: API keys, OAuth tokens, GitHub tokens, private key blocks, and generic `key=value`-style secrets are replaced with `[REDACTED]` before they can reach a client or disk. |
| Command injection | `tools/package_tools.py` | Package names are validated against a strict regex and passed as `subprocess` argv elements (never through a shell string). |
| Audit logging | `logging/audit.py` | Every tool call — success or failure — is appended to `AUDIT_LOG_PATH` with a request ID, principal, tool name, a redacted summary of arguments, and outcome. |
| No secrets in source | everywhere | All credentials come from environment variables (see `.env.example`); nothing sensitive is hard-coded, and `.env` is git-ignored. |

## What this server does *not* do

- It does not sandbox the code it executes beyond what the target
  kernel/runtime itself provides — anyone who can call `colab_execute_code`
  has the same power as anyone with a shell in that runtime. Treat the MCP
  connection itself as the trust boundary, and use `REQUIRE_AUTH` +
  `ALLOWED_TOOLS` to narrow what a given client can do.
- It does not implement Google OAuth today — the abstraction exists
  (`security/auth.py`), but only `none` and `api_key` modes are wired up.

## Reporting

Please open an issue (without attaching secrets or working exploits) if you
find a security problem in this server.
