# Troubleshooting

**`connection_error: Failed to connect to the Jupyter/Colab kernel runtime`**
No kernel could be started or attached to. If `COLAB_KERNEL_CONNECTION_FILE`
is unset, verify `ipykernel` is installed and a `python3` kernelspec exists
(`jupyter kernelspec list`). If it's set, verify the connection file exists,
is readable, and the kernel it describes is actually running and reachable.

**`runtime_unavailable_error: No kernel is connected`**
The session was closed or never connected. Call `colab_create_session` (or
just call any execute tool, which auto-creates a default session) again.

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
