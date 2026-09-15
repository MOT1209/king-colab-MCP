# Google Colab MCP Server

A standalone, framework-agnostic **[Model Context Protocol](https://modelcontextprotocol.io)**
server that lets *any* MCP-compatible AI agent or application control
Google Colab (or any Jupyter-compatible runtime) as an execution
environment — run code, manage notebooks, install packages, inspect
GPU/CPU/RAM, run training jobs, and manage files and artifacts.

```
Any AI Agent (KingAgent, Claude, Cursor, VS Code, a custom agent, ...)
      │
      │  MCP (stdio / SSE)
      ▼
Google Colab MCP Server   ←—— this repository
      │
      │  Jupyter kernel protocol
      ▼
Google Colab / any Jupyter-compatible runtime
```

This server has **no dependency on any specific agent or framework** —
not KingAgent, not Claude, not LangChain, CrewAI, AutoGen, or OpenAI
Agents. You can plug it into any of them without modifying this codebase.

## Features

- **40 MCP tools** across notebooks, code execution, files, packages,
  runtime/GPU introspection, ML training, and job/artifact management.
- **4 MCP resources**: `colab://runtime`, `colab://jobs`,
  `colab://notebooks`, `colab://artifacts`.
- **2 MCP prompts** guiding common multi-step workflows (GPU-aware
  execution, train-and-monitor).
- **Async job manager** for long-running work (training runs) — every
  tool that could take a while returns a `job_id` immediately instead of
  blocking.
- **Security layer**: auth, per-tool allow/deny lists, path sandboxing
  (both locally and inside the runtime), rate limiting, timeouts, secret
  redaction, and audit logging.
- **Structured errors** — every failure is `{"success": false, "error":
  {type, message, details, suggestion}}`, never a raw crash.
- **No framework lock-in on the Colab side either**: whatever ML
  framework your code imports (PyTorch, TensorFlow, Transformers,
  scikit-learn, XGBoost, ...) runs inside the target runtime — this
  server doesn't impose one.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Local kernel for dev/testing (no real Colab connection needed):
pip install ipykernel
python3 -m ipykernel install --user --name python3

cp .env.example .env
google-colab-mcp
```

Try it with the included example client:

```bash
python examples/example_client.py
```

Connect a real MCP client (any of them) by pointing it at the
`google-colab-mcp` command — see `config/mcp_client_example.json` and
[docs/SETUP.md](docs/SETUP.md) for a worked example, including how to
attach to a real Colab runtime via a Jupyter kernel connection file.

## Example: an agent using this server

```
Agent: "Run this code in Colab and use a GPU if one is available."
  → colab_get_runtime      # check active sessions / hardware
  → colab_get_gpu          # is a GPU present?
  → colab_execute_code     # run the code (device chosen accordingly)
  → colab_get_job/logs     # if it was a long training run instead
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Setup & Configuration](docs/SETUP.md)
- [Tool Reference](docs/TOOLS.md)
- [Security](docs/SECURITY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Development](docs/DEVELOPMENT.md)

## Testing

```bash
pytest -q
```

77 tests, including real end-to-end execution against a locally-launched
Jupyter kernel (skipped automatically if none is available).

## License

MIT — see [LICENSE](LICENSE).
