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

- `COLAB_KERNEL_CONNECTION_FILE` — path to a Jupyter kernel connection file
  to attach to a real Colab/Jupyter runtime. Leave empty to launch a local
  kernel (dev/test only).
- `COLAB_WORKSPACE_ROOT` — local sandbox for notebooks; nothing outside it
  is reachable by notebook tools.
- `COLAB_REMOTE_WORKSPACE_ROOT` — sandbox *inside the connected runtime*
  for file tools (default `/content/mcp_workspace`).
- `MAX_CONCURRENT_JOBS` — how many background jobs (training runs, etc.)
  may run at once.
- `REQUIRE_AUTH` / `COLAB_AUTH_MODE` / `MCP_AUTH_TOKEN` — see
  [SECURITY.md](SECURITY.md).

## Connecting to a real Google Colab runtime

Colab does not expose a public REST API for arbitrary execution; the
supported path is the standard Jupyter kernel protocol, which is exactly
what Colab's own "Connect to a local runtime" feature speaks. To attach
this server to an actual Colab GPU/TPU runtime:

1. Start (or have Colab start) a Jupyter kernel gateway reachable from
   wherever this server runs, and obtain its kernel connection file (host,
   ports, HMAC key — the JSON Jupyter writes when a kernel starts).
2. Set `COLAB_KERNEL_CONNECTION_FILE` to that file's path.
3. Start the server; `colab_get_runtime` / `colab_get_gpu` will report the
   real hardware once connected.

If you only need a sandboxed Python execution environment (not Colab's
specific hardware), omit `COLAB_KERNEL_CONNECTION_FILE` — the server
launches and manages its own local kernel automatically.

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
