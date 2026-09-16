"""Thin MCP wrappers around `colab/dataset_manager.py::DatasetManager`.

Scope: local upload + http(s) URL caching are fully implemented. Hugging
Face / Kaggle / Google Drive / GitHub connectors are not — see
docs/DATASETS.md and `DatasetSource` for why, and what a real connector
would need to implement.
"""
from __future__ import annotations

from typing import Any

from ..context import ServerContext
from .registry import ToolRegistry, ToolSpec


def _upload_dataset(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.dataset_manager.upload(args["name"], args["path"], args["content_base64"])


def _download_dataset(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.dataset_manager.download(args["name"], args.get("version"))


def _cache_dataset_from_url(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.dataset_manager.cache_from_url(args["name"], args["url"], args["path"])


def _validate_dataset(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.dataset_manager.validate(args["name"], args.get("version"))


def _inspect_dataset(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.dataset_manager.inspect(args["name"], args.get("version"), args.get("preview_bytes", 2000))


def _list_datasets(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return {"datasets": ctx.dataset_manager.list_datasets()}


def _convert_dataset_csv_to_json(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.dataset_manager.convert_csv_to_json(args["name"], args["output_path"], args.get("version"))


def register(registry: ToolRegistry) -> None:
    registry.register(ToolSpec(
        name="colab_upload_dataset",
        description="Register a dataset from base64-encoded content, stored in the server's local sandboxed dataset store (with a checksum and a version number).",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "path": {"type": "string", "description": "Relative storage path under the dataset root."},
                "content_base64": {"type": "string"},
            },
            "required": ["name", "path", "content_base64"],
        },
        handler=_upload_dataset,
    ))
    registry.register(ToolSpec(
        name="colab_cache_dataset_from_url",
        description="Download a dataset from an http(s) URL directly into the local dataset store and register it (with a checksum and a version number).",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "url": {"type": "string"},
                "path": {"type": "string", "description": "Relative storage path under the dataset root."},
            },
            "required": ["name", "url", "path"],
        },
        handler=_cache_dataset_from_url,
    ))
    registry.register(ToolSpec(
        name="colab_download_dataset",
        description="Download a registered dataset (or a specific version) as base64.",
        input_schema={
            "type": "object",
            "properties": {"name": {"type": "string"}, "version": {"type": "integer"}},
            "required": ["name"],
        },
        handler=_download_dataset,
    ))
    registry.register(ToolSpec(
        name="colab_validate_dataset",
        description="Recompute a dataset's checksum and compare it against what was recorded at registration time.",
        input_schema={
            "type": "object",
            "properties": {"name": {"type": "string"}, "version": {"type": "integer"}},
            "required": ["name"],
        },
        handler=_validate_dataset,
    ))
    registry.register(ToolSpec(
        name="colab_inspect_dataset",
        description="Get a dataset's metadata (size, checksum, source) and a text preview of its first bytes.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "integer"},
                "preview_bytes": {"type": "integer", "default": 2000},
            },
            "required": ["name"],
        },
        handler=_inspect_dataset,
    ))
    registry.register(ToolSpec(
        name="colab_list_datasets",
        description="List all registered datasets and their versions.",
        input_schema={"type": "object", "properties": {}},
        handler=_list_datasets,
    ))
    registry.register(ToolSpec(
        name="colab_convert_dataset_csv_to_json",
        description="Convert a registered CSV dataset to JSON and save it back into the dataset store.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "output_path": {"type": "string"},
                "version": {"type": "integer"},
            },
            "required": ["name", "output_path"],
        },
        handler=_convert_dataset_csv_to_json,
    ))
