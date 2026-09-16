# Architecture

```
Any MCP-compatible AI Agent (KingAgent, Claude, Cursor, custom, ...)
        │
        │  Model Context Protocol (stdio / SSE)
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        google-colab-mcp                          │
│                                                                   │
│  server/          MCP protocol wiring (tools/resources/prompts), │
│    app.py          transport-agnostic.                           │
│    protocol.py    auth → rate-limit → tool-permission →          │
│                     dangerous-tool-confirm → session-permission → │
│                     dispatch → audit, for every call.             │
│    transport.py   stdio (default) and SSE transports.             │
│                                                                   │
│  tools/           One file per responsibility (59 tools total):   │
│    runtime_tools    sessions (create/get/list/reconnect/close/     │
│                      health), GPU/CPU/RAM/disk, restart            │
│    execution_tools  run/interrupt code                            │
│    notebook_tools    create/read/update/execute .ipynb            │
│    file_tools        remote-runtime workspace file I/O            │
│    package_tools     pip install/list/export/profiles (thin        │
│                       wrapper over EnvironmentManager)             │
│    dataset_tools     upload/cache/validate/inspect/convert         │
│    training_tools    training jobs, eval, save/export             │
│    job_tools         status/logs/cancel/pause/resume/artifacts      │
│                                                                   │
│  colab/           Runtime abstraction:                            │
│    providers/       RuntimeProvider → colab (verified) /          │
│                       local_jupyter / remote_jupyter / docker      │
│    runtime_backend   RuntimeBackend interface each provider hands  │
│    kernel_client     back once connected (Jupyter protocol via     │
│    docker_backend    jupyter_client, or a Docker-hosted kernel).   │
│    session_manager   Sessions: id, runtime_id, provider, status,   │
│                       owner, permissions, created_at/last_activity.│
│    health_monitor    background health checks + bounded reconnect. │
│    execution_manager runs code, truncates oversized output.        │
│    runtime_manager   GPU/CPU/RAM/disk via multi-method in-kernel   │
│                       snippets (nvidia-smi/pynvml/torch/TF for GPU).│
│    notebook_manager  nbformat-based .ipynb CRUD.                   │
│    remote_fs         file ops *inside* the runtime, size-capped.   │
│    environment_manager  pip + EnvironmentProfile save/apply.       │
│    dataset_manager   checksummed, versioned dataset store +        │
│                       http(s) caching; HF/Kaggle/Drive/GitHub are   │
│                       documented, NotImplemented extension points.  │
│    artifact_manager  tracks per-job artifacts.                     │
│                                                                   │
│  jobs/            Async job engine: queued → starting → running →  │
│                    paused ⇄ running → completed/failed/cancelled/   │
│                    timeout. Every job records session_id,           │
│                    runtime_id, and structured metrics, not just     │
│                    free-text logs.                                  │
│                                                                   │
│  security/        auth, per-tool *and* per-session allow/deny       │
│                    lists, dangerous-tool confirmation policy,       │
│                    path sandboxing, output/file size limits,        │
│                    rate limiting, secret redaction.                 │
│  logging/         structured JSON logs + audit trail.               │
│  config/          environment-variable driven settings.             │
└─────────────────────────────────────────────────────────────────┘
        │
        │  Jupyter kernel protocol (ZeroMQ) — or a Docker exec for the
        │  docker provider
        ▼
   Verified Google Colab runtime  /  local or remote Jupyter kernel  /
   a disposable Docker-hosted kernel
```

## RuntimeProvider: the seam between tools and execution

```
MCP Tool → Runtime Manager (tools/runtime_tools.py etc.) → RuntimeProvider → RuntimeBackend
```

No tool constructs a `RuntimeBackend` directly, and no tool knows which
provider backs a session it's given a `session_id` for. `SessionManager`
resolves `provider` (a string: `colab`/`local_jupyter`/`remote_jupyter`/
`docker`) against `colab/providers/PROVIDER_REGISTRY`, and
`RuntimeProvider.connect()` drives one shared lifecycle
(`discovering → connecting → authenticating → initializing → ready`,
falling to `failed` on any error) regardless of which provider it is.
See [docs/RUNTIME_PROVIDERS.md](RUNTIME_PROVIDERS.md) for each provider's
specifics, and [docs/COLAB.md](COLAB.md) for why `ColabProvider` verifies
genuineness post-connect instead of trusting the `provider: "colab"`
argument at face value.

## Why the Jupyter kernel protocol, not a "Colab API"

Google Colab does not publish a REST API for arbitrary remote code
execution. The one documented, stable integration point is the Jupyter
kernel protocol — it's exactly what Colab's own "Connect to a local
runtime" feature speaks. `colab/kernel_client.py::JupyterKernelBackend`
implements a `RuntimeBackend` against that protocol via `jupyter_client`;
`colab/docker_backend.py::DockerJupyterBackend` implements the same
interface for a Docker-hosted kernel. A future backend is a new
`RuntimeBackend` implementation behind a new `RuntimeProvider` — no
existing tool code changes.

## Request lifecycle

Every tool call goes through `server/protocol.py::dispatch_tool_call`:

1. **Authenticate** the caller (`security/auth.py`).
2. **Rate-limit** per principal (`security/rate_limit.py`).
3. **Authorize** the tool server-wide against allow/deny lists
   (`security/permissions.py::check_tool_permission`).
4. **Confirm** if the tool is on the dangerous-tools list and
   `DANGEROUS_TOOLS_REQUIRE_CONFIRM` is set
   (`security/dangerous_tools.py`).
5. **Authorize** the tool against the *target session's* own permissions,
   if it names one (`security/permissions.py::check_session_tool_permission`).
6. **Dispatch** to the tool's handler, which uses `ServerContext` to reach
   the Colab/job managers. Path-based tools go through `PathGuard`
   (`security/path_guard.py`) so nothing escapes the sandboxed workspace;
   execution output and remote file transfers are size-capped.
7. **Audit-log** the call (redacted) regardless of outcome.
8. **Format** any exception as
   `{"success": false, "error": {type, message, details, suggestion,
   retryable}}` — the server never lets an exception escape as a raw 500
   or crash.

## Long-running work

Training runs, batch notebook executions, and anything else that could
run past a few seconds go through `jobs/job_manager.py` instead of
blocking the MCP call: the tool returns a `job_id` immediately, and the
caller polls `colab_get_job` / `colab_get_logs`, pauses/resumes
cooperatively with `colab_pause_job`/`colab_resume_job` (see
[docs/TRAINING.md](TRAINING.md) for exactly what "cooperative" means),
or cancels with `colab_cancel_job`. Every job records which
`session_id`/`runtime_id` it ran against. Artifacts produced along the
way are registered with `colab/artifact_manager.py` and discoverable via
`colab_get_artifacts` or the `colab://artifacts` resource.

## Health monitoring

`colab/health_monitor.py::HealthMonitor` runs as a background thread
(on by default, `HEALTH_MONITOR_ENABLED`) checking every session's
provider-reported health and attempting a bounded number of reconnects
(`MAX_RECONNECT_ATTEMPTS`) before leaving a session `failed` for explicit
investigation via `colab_session_health` / `colab_reconnect_session`.
