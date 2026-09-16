# Internal Audit — v0.1.0 baseline

Written before the v0.2 "Universal Colab Runtime" rework, based on reading
every source file (not the README). Findings are stated as facts (checked
against code), not assumptions.

## Critical

1. **No real distinction between "Colab" and "any Jupyter kernel".**
   `colab/kernel_client.py::JupyterKernelBackend` is a generic Jupyter
   client. Every tool, error message, and resource name says "Colab", but
   nothing ever checks whether the connected kernel is actually running on
   Google Colab. A user pointing `COLAB_KERNEL_CONNECTION_FILE` at a plain
   local Jupyter install gets `colab_get_runtime` results that look
   identical to a real Colab GPU session. This is the exact anti-pattern
   the new spec calls out ("لا تسمِّ أي runtime باسم Colab لمجرد أنه
   Jupyter-compatible").
2. **Single hard-coded backend.** `SessionManager` takes a
   `backend_factory` but the only production implementation is
   `JupyterKernelBackend`. There is no `RuntimeProvider` concept, so a
   Docker-based runtime or a genuinely Colab-specific connection path (with
   Colab-specific auth/health semantics) cannot be added without touching
   every call site that constructs a backend.
3. **No session lifecycle beyond connected/disconnected.**
   `SessionInfo` has no state machine — `backend.is_connected` is the only
   signal. There's no `discover → connect → authenticate → initialize →
   ready → running/idle → disconnected/failed → reconnecting`, no health
   monitoring, and no automatic reconnect. A kernel that dies mid-session
   is only noticed on the next `execute()` call, which then raises a
   generic `RuntimeUnavailableError`.

## High

4. **Errors have no `retryable` flag and no provider/network/auth-specific
   subtypes** beyond what `utils/errors.py` already has. A client cannot
   tell "retry this" from "don't bother" without string-matching
   `error.type`.
5. **Jobs don't record `session_id` / `runtime_id` / `metrics`.**
   `training_tools.py` stuffs `session_id` into `job.metadata` ad hoc;
   there's no `paused` state, and "metrics" (e.g. loss curves) have nowhere
   structured to go — only free-text log lines.
6. **No GPU detection redundancy.** `runtime_manager.py`'s GPU snippet
   only tries `torch.cuda`. A TensorFlow-only or no-torch runtime reports
   `available: false` even with a real GPU present.
7. **No environment/dataset management.** Package tools are pure
   install/uninstall/list; there's no way to snapshot/restore an
   environment (`EnvironmentProfile`) or to manage datasets beyond raw
   file I/O.
8. **Security is coarse-grained.** `ALLOWED_TOOLS`/`DENIED_TOOLS` is
   server-wide, not per-session. There is no "dangerous tool" concept
   (e.g. `colab_execute_code`, `colab_install_package`,
   `colab_delete_file` are exactly as gated as `colab_get_cpu`), no output
   size limits, and no execution resource quotas.

## Medium

9. **Authentication is API-key-only in practice.** `security/auth.py`'s
   `Principal` doesn't carry per-session permissions, and there is no
   token-rotation/expiration handling even though `.env.example` implies
   `google_oauth`/`service_account` are selectable modes (they raise
   `AuthenticationError` immediately).
10. **Docs oversell connectivity.** `docs/SETUP.md` describes attaching to
    "a real Colab runtime" via a connection file as if it were verified;
    it never was — only a local `ipykernel` was ever exercised in tests
    or CI. `README.md` repeats "Google Colab" throughout without
    qualifying that, today, this is really "Jupyter runtime, optionally
    one that happens to run on Colab infrastructure."
11. **`colab://environments`, `colab://datasets` resources don't exist**
    despite being implied by the project's stated ambitions.

## Low / cleanup

12. `resources/resources.py` reads `.rglob("*.ipynb")` on every
    `colab://notebooks` read — fine at current scale, worth revisiting if
    workspace grows large.
13. `RemoteFileManager` and `runtime_manager.py` both hand-build Python
    snippets with a private "marker" protocol; this works but has no
    shared helper, so each new snippet risks a copy-paste marker bug.

## What is *not* broken (verified, keep as-is)

- The security fundamentals that exist — `PathGuard`, `RateLimiter`,
  `redact_secrets`, `AuditLogger`, structured error envelopes — are sound
  and reused rather than rewritten in v0.2.
- The MCP wiring in `server/app.py` (lowlevel `Server`, stdio/SSE
  transports) is correct and was verified against a real MCP client
  round-trip; kept as the transport layer.
- `jobs/job_manager.py`'s thread+semaphore model is a reasonable base for
  the "production-grade" async job engine; it is extended, not replaced.
