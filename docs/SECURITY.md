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
| Authentication | `security/auth.py` | `REQUIRE_AUTH=true` + `COLAB_AUTH_MODE=api_key` enforces a constant-time-compared bearer token (`MCP_AUTH_TOKEN`). The abstraction (`Principal`/`authenticate()`) is designed so Google OAuth or service-account modes can be added later without touching tool code — see [AUTHENTICATION.md](AUTHENTICATION.md) for exactly what's implemented vs. designed-only. |
| Server-wide tool authorization | `security/permissions.py::check_tool_permission` | `ALLOWED_TOOLS` / `DENIED_TOOLS` env vars restrict which tools a deployment exposes at all. |
| Per-session tool authorization | `security/permissions.py::check_session_tool_permission` | A session created with a non-empty `permissions` list is restricted to those tools regardless of the server-wide lists — lets an agent hand a narrowly-scoped session to a less-trusted sub-task. |
| Dangerous-tool confirmation | `security/dangerous_tools.py` | With `DANGEROUS_TOOLS_REQUIRE_CONFIRM=true`, any tool that executes code or is destructive (`colab_execute_code`, `colab_delete_file`, `colab_restart_runtime`, `colab_install_package`, ...) is refused (`ApprovalRequiredError`) unless called with `"confirm": true`. |
| Path sandboxing | `security/path_guard.py`, `colab/remote_fs.py`, `colab/dataset_manager.py` | Notebook/local/dataset file paths are resolved against their configured root and rejected if they'd escape it (`PathAccessError`). Remote (in-runtime) file paths are confined to `COLAB_REMOTE_WORKSPACE_ROOT` the same way. |
| Output/file size limits | `colab/execution_manager.py`, `colab/remote_fs.py`, `colab/dataset_manager.py` | `MAX_OUTPUT_BYTES` truncates oversized stdout/stderr; `MAX_FILE_SIZE_BYTES` rejects oversized uploads/downloads/dataset caching *before* the bytes are sent through the kernel protocol, not after. |
| Rate limiting | `security/rate_limit.py` | Sliding-window limiter per principal, `MAX_REQUESTS_PER_MINUTE`. |
| Timeouts | every execution tool | `colab_execute_code`, notebook execution, and jobs all take `timeout_seconds` and enforce it; a hung kernel raises `ExecutionTimeoutError` (marked `retryable: true`) instead of hanging the MCP call forever. |
| Secret redaction | `security/redact.py` | Applied to every tool error, log line, and audit entry: API keys, OAuth tokens, GitHub tokens, private key blocks, and generic `key=value`-style secrets are replaced with `[REDACTED]` before they can reach a client or disk. |
| Command injection | `colab/environment_manager.py` | Package names are validated against a strict regex and passed as `subprocess` argv elements (never through a shell string). |
| SSRF exposure (documented, partially mitigated) | `colab/dataset_manager.py::cache_from_url` | Only `http(s)://` is fetched, and downloads are size-capped — but there is **no** IP allow/deny list or DNS-rebinding protection. Read [DATASETS.md](DATASETS.md)'s security note before exposing this tool to untrusted callers. |
| Audit logging | `logging/audit.py` | Every tool call — success or failure — is appended to `AUDIT_LOG_PATH` with a request ID, principal, tool name, a redacted summary of arguments, and outcome. |
| No secrets in source | everywhere | All credentials come from environment variables (see `.env.example`); nothing sensitive is hard-coded, and `.env` is git-ignored. |

## Colab-specific: the honesty guarantee

`ColabProvider` verifies, post-connect, that a session claiming
`provider: "colab"` is genuinely running on Colab infrastructure, and
refuses the connection (`ColabUnavailableError`) if it isn't — see
[COLAB.md](COLAB.md). This is a correctness/trust control as much as a
security one: an agent or downstream system deciding what to run based on
`colab_get_runtime` reporting "Colab" (e.g. "this has a real GPU, submit
the big training job") must not be lied to by a plain local kernel
answering the same protocol.

## What this server does *not* do

- It does not sandbox the code it executes beyond what the target
  kernel/runtime itself provides — anyone who can call `colab_execute_code`
  has the same power as anyone with a shell in that runtime. Treat the MCP
  connection itself as the trust boundary, and use `REQUIRE_AUTH` +
  `ALLOWED_TOOLS`/per-session `permissions` to narrow what a given client
  or session can do.
- It does not implement Google OAuth or service-account auth today — the
  abstraction exists (`security/auth.py`), but only `none` and `api_key`
  modes are wired up. See [AUTHENTICATION.md](AUTHENTICATION.md).
- It does not protect `colab_cache_dataset_from_url` against SSRF beyond
  scheme/size restrictions — no private-IP blocking, no DNS-rebinding
  defense. See [DATASETS.md](DATASETS.md).
- `colab_pause_job`/`colab_resume_job` are cooperative bookkeeping, not a
  guaranteed halt of in-kernel execution — see [TRAINING.md](TRAINING.md).

## Reporting

Please open an issue (without attaching secrets or working exploits) if you
find a security problem in this server.
