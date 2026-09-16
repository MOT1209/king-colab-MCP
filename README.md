# Google Colab MCP Server

A standalone, framework-agnostic, production-grade **[Model Context
Protocol](https://modelcontextprotocol.io)** server that lets *any*
MCP-compatible AI agent or application control Google Colab — or any
Jupyter-compatible runtime — as an execution environment: run code, manage
notebooks, install packages, inspect GPU/CPU/RAM/disk, run training jobs,
manage datasets and environment profiles, and track artifacts.

```
Any AI Agent (KingAgent, Claude, Cursor, VS Code, a custom agent, ...)
      │
      │  MCP (stdio / SSE)
      ▼
Google Colab MCP Server   ←—— this repository
      │
      ▼
Runtime Manager  →  Runtime Provider  →  Execution Backend
      │
      ▼
Google Colab (verified) / local Jupyter / remote Jupyter / Docker
```

This server has **no dependency on any specific agent or framework** —
not KingAgent, not Claude, not LangChain, CrewAI, AutoGen, or OpenAI
Agents. You can plug it into any of them without modifying this codebase.

## Google Colab is a first-class, *verified* provider

Colab has no public API for arbitrary remote execution; the only
documented path in is the Jupyter kernel protocol. Because a generic
Jupyter kernel and a real Colab kernel speak that same protocol, this
server **actively verifies** — after connecting — that a session created
with `provider: "colab"` is genuinely running on Colab (checking for
`google.colab`/Colab environment markers) and refuses the connection
otherwise, rather than silently treating any Jupyter kernel as "Colab"
the way most projects in this space do. See [docs/COLAB.md](docs/COLAB.md).

## Features

- **59 MCP tools** across runtime/session management, code execution,
  notebooks, files, packages/environments, GPU/hardware introspection, ML
  training, datasets, and jobs/artifacts.
- **7 MCP resources**: `colab://runtime`, `colab://sessions`,
  `colab://jobs`, `colab://notebooks`, `colab://artifacts`,
  `colab://environments`, `colab://datasets`.
- **RuntimeProvider abstraction** — `colab`, `local_jupyter`,
  `remote_jupyter`, `docker` — with a documented, honest lifecycle
  (`discovering → connecting → authenticating → initializing → ready →
  running/idle → disconnected/failed/reconnecting`) and a background
  health monitor with bounded auto-reconnect.
- **Async job engine** (`queued/starting/running/paused/completed/
  failed/cancelled/timeout`) with structured metrics, and each job
  tracks the session/runtime it ran on.
- **Environment & dataset management**: package install/list/export,
  reusable `EnvironmentProfile`s, and a checksummed, versioned dataset
  store with `http(s)://` caching.
- **Multi-method GPU detection** (nvidia-smi, pynvml, torch, TensorFlow)
  — not dependent on any one ML framework being installed.
- **Security layer**: auth, per-tool *and* per-session allow/deny lists,
  a dangerous-tool confirmation policy, path sandboxing (locally and
  inside the runtime), output/file size limits, rate limiting, timeouts,
  secret redaction, and audit logging.
- **Structured errors** with a `retryable` flag and provider/network/
  auth-specific categories — never a raw crash.
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
`google-colab-mcp` command — see `config/mcp_client_example.json`,
[docs/SETUP.md](docs/SETUP.md), and [docs/COLAB.md](docs/COLAB.md) for how
to attach to a real, verified Colab runtime.

## Example: an agent using this server

```
Agent: "Run this code in Colab and use a GPU if one is available."
  → colab_create_session (provider: "colab")
  → colab_get_runtime / colab_get_gpu   # is a GPU present?
  → colab_execute_code                  # run the code (device chosen accordingly)
  → colab_run_training / colab_get_job  # if it was a long training run instead
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Internal Audit](docs/AUDIT.md) — technical debt found before the v0.2 rework
- [Google Colab: what's actually verified](docs/COLAB.md)
- [Runtime Providers](docs/RUNTIME_PROVIDERS.md)
- [Authentication](docs/AUTHENTICATION.md)
- [Training](docs/TRAINING.md)
- [Datasets](docs/DATASETS.md)
- [Setup & Configuration](docs/SETUP.md)
- [Tool Reference](docs/TOOLS.md)
- [Security](docs/SECURITY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Development](docs/DEVELOPMENT.md)

## Testing

```bash
pytest -q
```

121 tests (unit + real end-to-end execution against a locally-launched
Jupyter kernel, skipped automatically if none is available), including a
dedicated test proving a plain Jupyter kernel is correctly rejected when
requested as `provider: "colab"`.

## License

MIT — see [LICENSE](LICENSE).
