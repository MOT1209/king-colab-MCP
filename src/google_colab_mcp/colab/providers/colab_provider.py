"""Google Colab, and *only* genuinely-verified Google Colab.

Colab has no public API for remote execution; the only documented path in
is the Jupyter kernel protocol (what Colab's own "Connect to a local
runtime" feature speaks). This provider therefore still connects via
`JupyterKernelBackend` — but unlike a plain Jupyter provider, it actively
verifies, after connecting, that the kernel it landed on is really running
on Colab infrastructure (via `google.colab` importability and Colab's own
environment markers). A connection that fails that check is never silently
reported as Colab: by default it raises `ColabUnavailableError` instead of
pretending. Set `config["strict"] = False` to allow an unverified
connection through anyway (useful for testing against a Colab-like stand-in)
— `verification["is_genuine_colab"]` still reports the truth either way.
"""
from __future__ import annotations

import json
from typing import Any, ClassVar

from ...utils.errors import ColabUnavailableError
from ..kernel_client import JupyterKernelBackend
from ..runtime_backend import RuntimeBackend
from .base import ProviderDiscoveryResult, RuntimeProvider

_VERIFY_SNIPPET = """
import json, os
info = {"is_colab_module": False, "markers": {}}
try:
    import google.colab  # noqa: F401
    info["is_colab_module"] = True
except Exception:
    pass
info["markers"]["COLAB_RELEASE_TAG"] = os.environ.get("COLAB_RELEASE_TAG")
info["markers"]["COLAB_GPU"] = os.environ.get("COLAB_GPU")
info["markers"]["content_dir_exists"] = os.path.isdir("/content")
print("__COLAB_VERIFY__" + json.dumps(info))
"""


class ColabProvider(RuntimeProvider):
    provider_id: ClassVar[str] = "colab"

    def discover(self) -> ProviderDiscoveryResult:
        connection_file = self.config.get("connection_file")
        if not connection_file:
            return ProviderDiscoveryResult(
                available=False,
                reason=(
                    "No 'connection_file' configured. Google Colab has no public API for remote "
                    "execution — you must supply the Jupyter kernel connection info for a real "
                    "Colab session (see docs/COLAB.md)."
                ),
            )
        return ProviderDiscoveryResult(available=True, metadata={"connection_file": connection_file})

    def _create_backend(self) -> RuntimeBackend:
        return JupyterKernelBackend(connection_file=self.config["connection_file"])

    def _verify(self, backend: RuntimeBackend) -> None:
        result = backend.execute(_VERIFY_SNIPPET, timeout=30)
        info: dict[str, Any] = {}
        for line in result.stdout.splitlines():
            if line.startswith("__COLAB_VERIFY__"):
                info = json.loads(line[len("__COLAB_VERIFY__"):])
                break

        is_genuine = bool(info.get("is_colab_module")) or bool(info.get("markers", {}).get("COLAB_RELEASE_TAG"))
        self.verification = {"is_genuine_colab": is_genuine, "checked": info}

        strict = self.config.get("strict", True)
        if not is_genuine and strict:
            backend.disconnect()
            raise ColabUnavailableError(
                "Connected kernel does not look like a real Google Colab runtime "
                "(no 'google.colab' module, no COLAB_RELEASE_TAG).",
                details=json.dumps(info),
                suggestion=(
                    "Point connection_file at an actual Colab kernel, or use the "
                    "'local_jupyter'/'remote_jupyter' provider instead if you just need a "
                    "generic Jupyter runtime. Pass strict=false to bypass this check for testing."
                ),
            )
