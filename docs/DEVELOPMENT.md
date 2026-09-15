# Development

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip install ipykernel && python3 -m ipykernel install --user --name python3
```

## Running tests

```bash
pytest                                  # full suite
pytest --cov=google_colab_mcp -q        # with coverage
pytest tests/test_integration_real_kernel.py  # real-kernel integration only
```

Unit tests use `FakeRuntimeBackend` (`tests/conftest.py`) so they run in
milliseconds with no real kernel. Integration tests in
`test_integration_real_kernel.py` launch a real local `ipykernel` and are
skipped automatically if one can't start.

## Adding a new tool

1. Pick the right module under `src/google_colab_mcp/tools/` by
   responsibility (or add a new module for a new category).
2. Write a handler `(ctx: ServerContext, args: dict) -> dict`. Raise a
   subclass of `ColabMCPError` (see `utils/errors.py`) for expected failure
   modes — the dispatcher formats it for you.
3. Register it with a `ToolSpec` (name, description, JSON Schema,
   handler) in that module's `register(registry)` function.
4. If it's a new module, add it to the import list in
   `tools/registry.py::build_default_registry`.
5. Add unit tests (against `FakeRuntimeBackend` via the `ctx` fixture) and,
   if it touches the runtime meaningfully, a real-kernel integration test.

## Adding a new runtime backend

Implement `colab/runtime_backend.py::RuntimeBackend` and pass a factory to
`SessionManager(backend_factory=...)`. Nothing above the `RuntimeBackend`
interface needs to change.

## Code style

- No hard dependency on any AI agent framework, anywhere in `src/`.
- One tool = one responsibility; don't grow a tool into a multi-purpose
  Swiss-army handler.
- All file access goes through `PathGuard` or `remote_fs`'s `_safe_join` —
  never build a path by hand in a tool.
- Never interpolate user input into a shell string; use `subprocess` argv
  lists (see `tools/package_tools.py`).
