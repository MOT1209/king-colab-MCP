"""Abstract execution-runtime backend.

Google Colab does not expose a public REST API for arbitrary remote code
execution. The supported, documented way to reach a Colab (or any Jupyter)
compute backend programmatically is the standard Jupyter kernel protocol:
Colab's "Connect to a local runtime" feature is itself a Jupyter kernel
gateway conversation. This abstraction keeps that protocol detail behind
`RuntimeBackend` so a different backend (a hosted kernel gateway, a
service-account-authenticated Colab Enterprise runtime, etc.) can be dropped
in later without touching any tool code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionResult:
    stdout: str = ""
    stderr: str = ""
    result_repr: str | None = None
    display_data: list[dict[str, Any]] = field(default_factory=list)
    error: dict[str, Any] | None = None
    execution_count: int | None = None
    timed_out: bool = False


class RuntimeBackend(ABC):
    """One connected execution runtime (a Colab / Jupyter kernel)."""

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @property
    @abstractmethod
    def is_connected(self) -> bool: ...

    @abstractmethod
    def execute(self, code: str, timeout: float) -> ExecutionResult: ...

    @abstractmethod
    def interrupt(self) -> None: ...

    @abstractmethod
    def restart(self) -> None: ...

    @abstractmethod
    def kernel_info(self) -> dict[str, Any]: ...
