# Runtime Providers

```
MCP Tool → Runtime Manager (colab_*_tools) → RuntimeProvider → RuntimeBackend
```

No tool ever constructs a `RuntimeBackend` directly. `SessionManager`
resolves a `provider` string (`colab_create_session`'s `provider`
argument) against `colab/providers/PROVIDER_REGISTRY` and drives the
shared lifecycle in `RuntimeProvider.connect()`:

```
discovering → connecting → authenticating → initializing → ready
                                                 │
                                                 ▼ (on failure)
                                               failed
```

`ready` sessions transition to `running`/`idle` implicitly through use,
and to `reconnecting` when `SessionManager.reconnect()` (or the
background `HealthMonitor`) retries a dropped connection. See
`colab/providers/base.py::RuntimeState` for the full enum.

## Providers

| provider_id | What it connects to | Claims to be Colab? | Requires |
|---|---|---|---|
| `colab` | A Jupyter kernel, **verified** post-connect to be genuinely running on Colab (`google.colab` importable / `COLAB_RELEASE_TAG` set). Refuses to connect otherwise (see [COLAB.md](COLAB.md)). | Yes — and only if verified. | `provider_config.connection_file` |
| `local_jupyter` | A kernel this server launches itself via `ipykernel`. | No. | `ipykernel` installed |
| `remote_jupyter` | Any other Jupyter-protocol kernel (JupyterHub, a self-hosted gateway, ...). | No. | `provider_config.connection_file` pointing at an existing file |
| `docker` | A kernel launched inside a fresh, disposable Docker container. | No. | A reachable Docker daemon; Linux host networking (see limitation below) |

## Adding a new provider

Subclass `RuntimeProvider` (`colab/providers/base.py`):

```python
class MyProvider(RuntimeProvider):
    provider_id = "my_provider"

    def discover(self) -> ProviderDiscoveryResult:
        ...  # cheap check: can this even work with self.config right now?

    def _create_backend(self) -> RuntimeBackend:
        ...  # return a not-yet-connected RuntimeBackend

    def authenticate(self) -> None:
        ...  # optional: provider-specific auth before connecting

    def _verify(self, backend: RuntimeBackend) -> None:
        ...  # optional: post-connect verification (raise to refuse)
```

Register it in `colab/providers/__init__.py::PROVIDER_REGISTRY`. No other
file needs to change — every tool goes through `SessionManager`, which is
provider-agnostic.

## Docker provider: known limitation

`DockerProvider` starts the container with `--network host` so the
Jupyter connection file's ports (written on the host) are directly
reachable inside the container without port-mapping bookkeeping. This
works on Linux. **It does not work the same way on Docker Desktop for
macOS/Windows**, where the VM boundary means host networking doesn't
expose ports identically — this is a genuine, documented gap, not
something silently worked around. On those platforms, use
`local_jupyter` or `remote_jupyter` instead, or run this server itself
inside a Linux VM/container alongside Docker.

This provider is implemented and unit-tested for its discovery/error
paths (`docker_available()`, `discover()`), but the full container
lifecycle has **not** been integration-tested end-to-end in this
project's environment, which has no reachable Docker daemon — stated here
rather than left implicit.

## Health monitoring and reconnect

`colab/health_monitor.py::HealthMonitor` runs as a daemon thread
(`HEALTH_MONITOR_ENABLED`, default on; interval via
`HEALTH_CHECK_INTERVAL_SECONDS`) that calls `SessionManager.health_check`
for every session and, if unhealthy, calls `SessionManager.reconnect` up
to `MAX_RECONNECT_ATTEMPTS` times before leaving it `failed` for a human
or agent to investigate via `colab_session_health` /
`colab_reconnect_session`. The attempt counter only resets once a
*subsequent* health check reports healthy — not merely because a
`reconnect()` call didn't raise — so a provider whose connect() succeeds
but whose kernel is still unresponsive doesn't retry forever.
