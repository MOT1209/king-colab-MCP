"""Environment-driven configuration.

All configuration comes from environment variables (optionally loaded from a
`.env` file). Nothing sensitive is ever hard-coded in source. See
`.env.example` for the full list of supported variables.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    val = os.environ.get(name)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _list(name: str, default: list[str]) -> list[str]:
    val = os.environ.get(name)
    if not val:
        return default
    return [item.strip() for item in val.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    # Server / transport
    mcp_host: str = field(default_factory=lambda: os.environ.get("MCP_HOST", "127.0.0.1"))
    mcp_port: int = field(default_factory=lambda: _int("MCP_PORT", 8765))
    mcp_transport: str = field(default_factory=lambda: os.environ.get("MCP_TRANSPORT", "stdio"))
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))

    # Colab / runtime
    # Note: there is no single global "the" connection file — every session
    # picks its own provider/connection info via colab_create_session's
    # provider_config, since a server can hold multiple sessions against
    # different providers at once. See docs/RUNTIME_PROVIDERS.md.
    colab_auth_mode: str = field(default_factory=lambda: os.environ.get("COLAB_AUTH_MODE", "none"))
    colab_timeout: int = field(default_factory=lambda: _int("COLAB_TIMEOUT", 120))
    max_concurrent_jobs: int = field(default_factory=lambda: _int("MAX_CONCURRENT_JOBS", 4))

    # Security
    mcp_auth_token: str | None = field(default_factory=lambda: os.environ.get("MCP_AUTH_TOKEN") or None)
    require_auth: bool = field(default_factory=lambda: _bool("REQUIRE_AUTH", False))
    workspace_root: Path = field(
        default_factory=lambda: Path(os.environ.get("COLAB_WORKSPACE_ROOT", "./workspace")).resolve()
    )
    allowed_tools: list[str] = field(default_factory=lambda: _list("ALLOWED_TOOLS", []))
    denied_tools: list[str] = field(default_factory=lambda: _list("DENIED_TOOLS", []))
    max_requests_per_minute: int = field(default_factory=lambda: _int("MAX_REQUESTS_PER_MINUTE", 60))
    max_code_length: int = field(default_factory=lambda: _int("MAX_CODE_LENGTH", 200_000))
    audit_log_path: Path = field(
        default_factory=lambda: Path(os.environ.get("AUDIT_LOG_PATH", "./logs/audit.log")).resolve()
    )

    # Remote filesystem sandbox (inside the connected Colab/Jupyter runtime)
    remote_workspace_root: str = field(
        default_factory=lambda: os.environ.get("COLAB_REMOTE_WORKSPACE_ROOT", "/content/mcp_workspace")
    )

    # Artifacts
    artifact_root: Path = field(
        default_factory=lambda: Path(os.environ.get("COLAB_ARTIFACT_ROOT", "./workspace/artifacts")).resolve()
    )
    notebook_root: Path = field(
        default_factory=lambda: Path(os.environ.get("COLAB_NOTEBOOK_ROOT", "./workspace/notebooks")).resolve()
    )
    environment_root: Path = field(
        default_factory=lambda: Path(os.environ.get("COLAB_ENVIRONMENT_ROOT", "./workspace/environments")).resolve()
    )
    dataset_root: Path = field(
        default_factory=lambda: Path(os.environ.get("COLAB_DATASET_ROOT", "./workspace/datasets")).resolve()
    )

    # Health monitoring / reconnect
    health_monitor_enabled: bool = field(default_factory=lambda: _bool("HEALTH_MONITOR_ENABLED", True))
    health_check_interval_seconds: float = field(
        default_factory=lambda: float(_int("HEALTH_CHECK_INTERVAL_SECONDS", 30))
    )
    max_reconnect_attempts: int = field(default_factory=lambda: _int("MAX_RECONNECT_ATTEMPTS", 3))

    # Dangerous-tool policy
    dangerous_tools_require_confirm: bool = field(
        default_factory=lambda: _bool("DANGEROUS_TOOLS_REQUIRE_CONFIRM", False)
    )
    max_output_bytes: int = field(default_factory=lambda: _int("MAX_OUTPUT_BYTES", 2_000_000))
    max_file_size_bytes: int = field(default_factory=lambda: _int("MAX_FILE_SIZE_BYTES", 100_000_000))

    def ensure_dirs(self) -> None:
        for d in (
            self.workspace_root,
            self.artifact_root,
            self.notebook_root,
            self.environment_root,
            self.dataset_root,
            self.audit_log_path.parent,
        ):
            d.mkdir(parents=True, exist_ok=True)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings
