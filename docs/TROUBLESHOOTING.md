# Troubleshooting

**`connection_error: Failed to connect to the Jupyter/Colab kernel runtime`**
No kernel could be started or attached to. For `provider: "local_jupyter"`
(the default), verify `ipykernel` is installed and a `python3` kernelspec
exists (`jupyter kernelspec list`). For `colab`/`remote_jupyter`, verify
`provider_config.connection_file` exists, is readable, and the kernel it
describes is actually running and reachable.

**`colab_unavailable_error: Connected kernel does not look like a real Google Colab runtime`**
`ColabProvider` connected but couldn't verify `google.colab`/Colab
environment markers — see [COLAB.md](COLAB.md). This is intentional: it
means you pointed `provider: "colab"` at a kernel that isn't actually
Colab. Use `local_jupyter`/`remote_jupyter` if you don't need the Colab
claim, or pass `provider_config.strict: false` to connect anyway for
testing.

**`provider_error`**
A `RuntimeProvider`'s `discover()` reported it can't work right now (e.g.
`docker` with no reachable Docker daemon), or `connect()` failed for a
provider-specific reason. Check `error.details` and
[RUNTIME_PROVIDERS.md](RUNTIME_PROVIDERS.md) for that provider's
requirements.

**`runtime_unavailable_error: No kernel is connected`**
The session was closed or never connected. Call `colab_create_session` (or
just call any execute tool, which auto-creates a default `local_jupyter`
session) again — or `colab_reconnect_session` if it dropped mid-use.

**`timeout_error` on `colab_execute_code`**
The code ran longer than `timeout_seconds` (or `COLAB_TIMEOUT`). Either
raise the timeout or, for long training runs, switch to
`colab_run_training` (job-based, no per-call timeout ceiling beyond
`timeout_seconds` you set on the job itself).

**`package_error: pip install failed`**
Check `details` in the error for pip's real stderr — usually a genuine
resolution failure or missing system dependency inside the runtime, not a
bug in this server.

**`path_access_error`**
A file/notebook path resolved outside the configured sandbox
(`COLAB_WORKSPACE_ROOT` or `COLAB_REMOTE_WORKSPACE_ROOT`). Use a path
relative to that root; `..` and absolute paths are rejected by design.

**`authentication_error` / `authorization_error`**
Check `REQUIRE_AUTH`, `COLAB_AUTH_MODE`, `MCP_AUTH_TOKEN`, and
`ALLOWED_TOOLS`/`DENIED_TOOLS` in your environment. See
[SECURITY.md](SECURITY.md).

**Server logs**
Structured JSON logs go to stderr (stdout is reserved for the stdio MCP
transport). Every tool call also appends a redacted entry to
`AUDIT_LOG_PATH` with a `request_id` you can correlate against.
