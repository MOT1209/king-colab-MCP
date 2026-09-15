from __future__ import annotations

from typing import Any

from ..context import ServerContext
from .registry import ToolRegistry, ToolSpec


def _create_notebook(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.notebook_manager.create_notebook(args["path"], args.get("kernel_name", "python3"))


def _get_notebook(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.notebook_manager.get_notebook(args["path"])


def _update_notebook(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.notebook_manager.update_notebook(args["path"], args["cells"])


def _add_cell(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.notebook_manager.add_cell(
        args["path"], args["source"], args.get("cell_type", "code"), args.get("index")
    )


def _edit_cell(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.notebook_manager.edit_cell(args["path"], args["index"], args["source"])


def _delete_cell(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.notebook_manager.delete_cell(args["path"], args["index"])


def _execute_cell(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.notebook_manager.execute_cell(
        args["path"], args["index"], args.get("session_id"), args.get("timeout_seconds", ctx.settings.colab_timeout)
    )


def _execute_notebook(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.notebook_manager.execute_notebook(
        args["path"], args.get("session_id"), args.get("timeout_seconds", ctx.settings.colab_timeout)
    )


def _export_notebook(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.notebook_manager.export_notebook(args["path"], args.get("format", "ipynb"))


def register(registry: ToolRegistry) -> None:
    registry.register(ToolSpec(
        name="colab_create_notebook",
        description="Create a new, empty .ipynb notebook inside the sandboxed workspace.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Notebook path, relative to the workspace root."},
                "kernel_name": {"type": "string", "default": "python3"},
            },
            "required": ["path"],
        },
        handler=_create_notebook,
    ))
    registry.register(ToolSpec(
        name="colab_get_notebook",
        description="Read a notebook's cells and metadata.",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        handler=_get_notebook,
    ))
    registry.register(ToolSpec(
        name="colab_update_notebook",
        description="Replace a notebook's entire cell list.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "cells": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "cell_type": {"type": "string", "enum": ["code", "markdown"]},
                            "source": {"type": "string"},
                        },
                        "required": ["source"],
                    },
                },
            },
            "required": ["path", "cells"],
        },
        handler=_update_notebook,
    ))
    registry.register(ToolSpec(
        name="colab_add_cell",
        description="Add a single cell to a notebook, at an index or appended to the end.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "source": {"type": "string"},
                "cell_type": {"type": "string", "enum": ["code", "markdown"], "default": "code"},
                "index": {"type": "integer"},
            },
            "required": ["path", "source"],
        },
        handler=_add_cell,
    ))
    registry.register(ToolSpec(
        name="colab_edit_cell",
        description="Replace the source of one existing cell by index.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "index": {"type": "integer"},
                "source": {"type": "string"},
            },
            "required": ["path", "index", "source"],
        },
        handler=_edit_cell,
    ))
    registry.register(ToolSpec(
        name="colab_delete_cell",
        description="Delete one cell by index.",
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}, "index": {"type": "integer"}},
            "required": ["path", "index"],
        },
        handler=_delete_cell,
    ))
    registry.register(ToolSpec(
        name="colab_execute_cell",
        description="Execute a single notebook cell by index against a runtime session.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "index": {"type": "integer"},
                "session_id": {"type": "string"},
                "timeout_seconds": {"type": "number"},
            },
            "required": ["path", "index"],
        },
        handler=_execute_cell,
    ))
    registry.register(ToolSpec(
        name="colab_execute_notebook",
        description="Execute every code cell in a notebook, in order, against a runtime session.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "session_id": {"type": "string"},
                "timeout_seconds": {"type": "number"},
            },
            "required": ["path"],
        },
        handler=_execute_notebook,
    ))
    registry.register(ToolSpec(
        name="colab_export_notebook",
        description="Export a notebook as raw .ipynb JSON or as a flattened Python script.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "format": {"type": "string", "enum": ["ipynb", "python"], "default": "ipynb"},
            },
            "required": ["path"],
        },
        handler=_export_notebook,
    ))
