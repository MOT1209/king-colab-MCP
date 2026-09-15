# Architecture

```
Any MCP-compatible AI Agent (KingAgent, Claude, Cursor, custom, ...)
        │
        │  Model Context Protocol (stdio / SSE)
        ▼
┌───────────────────────────────────────────────────────────┐
│                    google-colab-mcp                        │
│                                                             │
│  server/            MCP protocol wiring (tools/resources/  │
│    app.py            prompts), transport-agnostic.          │
│    protocol.py      Auth → rate-limit → permission →       │
│                      dispatch → audit, for every call.     │
│    transport.py     stdio (default) and SSE transports.    │
│                                                             │
│  tools/             One file per responsibility:           │
│    notebook_tools    create/read/update/execute .ipynb     │
│    execution_tools   run/interrupt code                    │
│    file_tools        remote workspace file I/O             │
│    package_tools     pip install/uninstall/list            │
│    runtime_tools     sessions, GPU/CPU/RAM/disk, restart    │
│    training_tools    long training jobs, eval, save/export  │
│    job_tools         job status/logs/cancel/artifacts       │
│                                                             │
│  colab/             Runtime abstraction (no Colab-specific  │
│    runtime_backend   fake API — the real, documented way   │
│    kernel_client     to reach Colab/Jupyter compute is the  │
│    session_manager   standard Jupyter kernel protocol).     │
│    execution_manager                                        │
│    runtime_manager   GPU/CPU/RAM/disk introspection via      │
│                      small Python snippets run in-kernel.   │
│    notebook_manager  nbformat-based .ipynb CRUD.            │
│    remote_fs         file ops *inside* the runtime.         │
│    artifact_manager  tracks per-job artifacts.               │
│                                                             │
│  jobs/              Async job manager: queued → starting → │
│                      running → completed/failed/cancelled/  │
│                      timeout. Every long-running tool        │
│                      returns a job_id immediately.           │
│                                                             │
│  security/          auth, per-tool allow/deny lists,         │
│                      path sandboxing, rate limiting,         │
│                      secret redaction.                       │
│  logging/           structured JSON logs + audit trail.      │
│  config/            environment-variable driven settings.    │
└───────────────────────────────────────────────────────────┘
        │
        │  Jupyter kernel protocol (ZeroMQ)
        ▼
   Google Colab runtime  /  any Jupyter-compatible kernel
```

## Why the Jupyter kernel protocol, not a "Colab API"

Google Colab does not publish a REST API for arbitrary remote code
execution. The one documented, stable integration point is the Jupyter
kernel protocol — it's exactly what Colab's own "Connect to a local
runtime" feature speaks. `colab/kernel_client.py` implements a
`RuntimeBackend` against that protocol via `jupyter_client`, so:

- Attaching to a real Colab session means pointing
  `COLAB_KERNEL_CONNECTION_FILE` at that session's kernel connection info.
- Local development and CI need no network access at all: omitting the
  connection file launches an ordinary local kernel via `ipykernel`.
- A future backend (Colab Enterprise, a hosted kernel gateway, etc.) is a
  new `RuntimeBackend` implementation — no tool code changes.

## Request lifecycle

Every tool call goes through `server/protocol.py::dispatch_tool_call`:

1. **Authenticate** the caller (`security/auth.py`).
2. **Rate-limit** per principal (`security/rate_limit.py`).
3. **Authorize** the specific tool against allow/deny lists
   (`security/permissions.py`).
4. **Dispatch** to the tool's handler, which uses `ServerContext` to reach
   the Colab/job managers. Path-based tools go through `PathGuard`
   (`security/path_guard.py`) so nothing escapes the sandboxed workspace.
5. **Audit-log** the call (redacted) regardless of outcome.
6. **Format** any exception as
   `{"success": false, "error": {type, message, details, suggestion}}` —
   the server never lets an exception escape as a raw 500 or crash.

## Long-running work

Training runs, batch notebook executions, and anything else that could
run past a few seconds go through `jobs/job_manager.py` instead of
blocking the MCP call: the tool returns a `job_id` immediately, and the
caller polls `colab_get_job` / `colab_get_logs`, or cancels with
`colab_cancel_job`. Artifacts produced along the way are registered with
`colab/artifact_manager.py` and discoverable via `colab_get_artifacts` or
the `colab://artifacts` resource.
