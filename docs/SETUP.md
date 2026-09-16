# Setup & Configuration

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

For local development without a real Colab connection, install a local
kernelspec so the server can launch its own kernel:

```bash
pip install ipykernel
python3 -m ipykernel install --user --name python3
```

## Configuration

All configuration is environment-variable driven — see `.env.example` for
the full list. Copy it to `.env` and edit:

```bash
cp .env.example .env
```

Key variables:

- `COLAB_WORKSPACE_ROOT` — local sandbox for notebooks; nothing outside it
  is reachable by notebook tools.
- `COLAB_REMOTE_WORKSPACE_ROOT` — sandbox *inside the connected runtime*
  for file tools (default `/content/mcp_workspace`).
- `COLAB_ENVIRONMENT_ROOT` / `COLAB_DATASET_ROOT` — local sandboxes for
  saved `EnvironmentProfile`s and the dataset store.
- `MAX_CONCURRENT_JOBS` — how many background jobs (training runs, etc.)
  may run at once.
- `HEALTH_MONITOR_ENABLED` / `HEALTH_CHECK_INTERVAL_SECONDS` /
  `MAX_RECONNECT_ATTEMPTS` — background session health checks and
  bounded auto-reconnect; see [RUNTIME_PROVIDERS.md](RUNTIME_PROVIDERS.md).
- `DANGEROUS_TOOLS_REQUIRE_CONFIRM` — require `{"confirm": true}` on
  destructive/execution tools; see [SECURITY.md](SECURITY.md).
- `REQUIRE_AUTH` / `COLAB_AUTH_MODE` / `MCP_AUTH_TOKEN` — see
  [SECURITY.md](SECURITY.md) and [AUTHENTICATION.md](AUTHENTICATION.md).

There is no single global connection file anymore — sessions are created
per-call via `colab_create_session`, each choosing its own provider.

## Connecting to a real Google Colab runtime

Colab does not expose a public REST API for arbitrary execution; the
supported path is the standard Jupyter kernel protocol, which is exactly
what Colab's own "Connect to a local runtime" feature speaks. To attach
this server to an actual Colab GPU/TPU runtime:

1. Start (or have Colab start) a Jupyter kernel gateway reachable from
   wherever this server runs, and obtain its kernel connection file (host,
   ports, HMAC key — the JSON Jupyter writes when a kernel starts).
2. Call `colab_create_session` with
   `{"provider": "colab", "provider_config": {"connection_file": "/path/to/kernel.json"}}`.
   The server verifies the kernel is genuinely Colab before the session is
   created — see [COLAB.md](COLAB.md) for exactly what that check does and
   why it exists.
3. `colab_get_runtime` / `colab_get_gpu` against that `session_id` will
   report the real hardware once connected.

If you only need a sandboxed Python execution environment (not
specifically Colab's hardware), call `colab_create_session` with
`{"provider": "local_jupyter"}` (or omit `provider` entirely — every tool
that takes a `session_id` also falls back to a lazily-created default
`local_jupyter` session if you never call `colab_create_session` at all).

## Running the server

```bash
google-colab-mcp                 # stdio transport (default)
google-colab-mcp --transport sse # SSE transport, MCP_HOST/MCP_PORT
```

Or via the helper script: `./scripts/run_server.sh`.

## Connecting an MCP client

Any MCP-compatible client works. Example (`config/mcp_client_example.json`)
for a client that reads a `mcpServers` map (Claude Desktop-style config):

```json
{
  "mcpServers": {
    "google-colab": {
      "command": "google-colab-mcp",
      "args": [],
      "env": { "COLAB_WORKSPACE_ROOT": "./workspace" }
    }
  }
}
```

See `examples/example_client.py` for a minimal, framework-agnostic Python
client using the official `mcp` SDK directly.

## Docker

```bash
docker build -t google-colab-mcp .
docker run --rm -i --env-file .env google-colab-mcp
```
