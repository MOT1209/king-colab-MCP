"""A small, explicit tool registry.

Each tool is one narrow responsibility (never "one tool that does
everything"). A `ToolSpec` bundles the MCP-facing name/description/schema
with the Python handler that implements it. Handlers receive a
`ServerContext` and a validated arguments dict, and return a plain JSON-able
dict — the MCP layer wraps that as the tool result, and wraps exceptions as
the structured `{"success": false, "error": {...}}` shape.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..context import ServerContext

ToolHandler = Callable[[ServerContext, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Duplicate tool registration: {spec.name}")
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def all(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def names(self) -> list[str]:
        return list(self._tools.keys())


def build_default_registry() -> ToolRegistry:
    """Import and register every tool module. Kept in one place so the
    server module doesn't need to know the individual tool file names."""
    registry = ToolRegistry()

    from . import (
        dataset_tools,
        execution_tools,
        file_tools,
        job_tools,
        notebook_tools,
        package_tools,
        runtime_tools,
        training_tools,
    )

    for module in (
        notebook_tools,
        execution_tools,
        file_tools,
        package_tools,
        runtime_tools,
        training_tools,
        job_tools,
        dataset_tools,
    ):
        module.register(registry)

    return registry
