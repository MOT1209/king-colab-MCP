# Google Colab: what this server actually does

Google Colab has **no public REST API for arbitrary remote code
execution.** The only documented, supported way in is the Jupyter kernel
protocol — the same one Colab's own "Connect to a local runtime" feature
speaks. Everything this server does with Colab goes through that
protocol via `ColabProvider` (`src/google_colab_mcp/colab/providers/colab_provider.py`).

## The honesty guarantee

A generic Jupyter kernel and a real Colab kernel speak the identical wire
protocol — nothing about the protocol itself proves which one you're
talking to. Earlier versions of this project (and most "Colab MCP"
projects) call every Jupyter kernel "Colab" because of this. **This server
does not.**

When you connect with `provider: "colab"`, after the kernel connects,
`ColabProvider` runs a verification snippet inside it checking for:

- an importable `google.colab` module, and/or
- Colab-specific environment markers (`COLAB_RELEASE_TAG`, `COLAB_GPU`, an
  existing `/content` directory).

If neither is present, the connection is refused with
`ColabUnavailableError` — the session is **not** created, and
`colab_get_runtime`/`colab_get_session` will never claim it as Colab. Set
`provider_config.strict = false` on `colab_create_session` to allow an
unverified connection through anyway (useful for testing against a
Colab-like stand-in); `verification.is_genuine_colab` in the session's
health/status output still reports the truth either way.

If you just want a sandboxed Python execution environment and don't care
whether it's specifically Colab, use `provider: "local_jupyter"` or
`"remote_jupyter"` instead — they never make a Colab claim in the first
place, so there's nothing to verify.

## Connecting to a real Colab session

1. Obtain the target Colab kernel's Jupyter connection info (host, ports,
   HMAC key — the JSON a Jupyter kernel writes on startup) reachable from
   wherever this server runs.
2. Call `colab_create_session` with:
   ```json
   {
     "provider": "colab",
     "provider_config": { "connection_file": "/path/to/kernel-connection.json" }
   }
   ```
3. Check the response's `status` and, if you want the verification detail,
   call `colab_session_health` — its `verification.is_genuine_colab` field
   is the authoritative answer.

## What is verified vs. not, honestly

| Claim | Status |
|---|---|
| Connecting to a real Colab kernel via a connection file works | **Verified against the Jupyter protocol itself** (real kernel roundtrips are integration-tested), but **not against an actual colab.research.google.com session** — that requires a live Google account and Colab UI interaction this test environment doesn't have. |
| A plain local/self-hosted Jupyter kernel is correctly rejected as "not Colab" | **Verified** — `tests/test_integration_real_kernel.py::test_real_colab_provider_rejects_non_colab_kernel` does exactly this against a real local kernel. |
| GPU/CPU/RAM introspection works on Colab's actual hardware | Not directly verified (no GPU in the CI/dev sandbox); the detection code itself (`runtime_manager.py`) is exercised against a real (GPU-less) kernel and degrades to `available: false` correctly when no GPU is present, via multiple independent methods (nvidia-smi, pynvml, torch, TensorFlow). |
