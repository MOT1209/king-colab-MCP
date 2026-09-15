from __future__ import annotations

import base64
from typing import Any

from ..context import ServerContext
from .registry import ToolRegistry, ToolSpec


def _upload_file(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.remote_file_manager.upload_file(args["path"], args["content_base64"], args.get("session_id"))


def _download_file(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.remote_file_manager.download_file(args["path"], args.get("session_id"))


def _list_files(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.remote_file_manager.list_files(args.get("path", ""), args.get("session_id"))


def _read_file(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.remote_file_manager.read_file(args["path"], args.get("session_id"))


def _write_file(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.remote_file_manager.write_file(args["path"], args["content"], args.get("session_id"))


def _delete_file(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.remote_file_manager.delete_file(args["path"], args.get("session_id"))


def _move_file(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.remote_file_manager.move_file(args["source"], args["destination"], args.get("session_id"))


def _create_directory(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.remote_file_manager.create_directory(args["path"], args.get("session_id"))


def register(registry: ToolRegistry) -> None:
    remote_note = " Path is relative to the runtime's sandboxed workspace (e.g. /content/mcp_workspace)."

    registry.register(ToolSpec(
        name="colab_upload_file",
        description="Upload base64-encoded file content into the runtime's sandboxed workspace." + remote_note,
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content_base64": {"type": "string"},
                "session_id": {"type": "string"},
            },
            "required": ["path", "content_base64"],
        },
        handler=_upload_file,
    ))
    registry.register(ToolSpec(
        name="colab_download_file",
        description="Download a file from the runtime's sandboxed workspace as base64." + remote_note,
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}, "session_id": {"type": "string"}},
            "required": ["path"],
        },
        handler=_download_file,
    ))
    registry.register(ToolSpec(
        name="colab_list_files",
        description="List files and directories under a path in the runtime's sandboxed workspace." + remote_note,
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string", "default": ""}, "session_id": {"type": "string"}},
        },
        handler=_list_files,
    ))
    registry.register(ToolSpec(
        name="colab_read_file",
        description="Read a text file's contents from the runtime's sandboxed workspace." + remote_note,
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}, "session_id": {"type": "string"}},
            "required": ["path"],
        },
        handler=_read_file,
    ))
    registry.register(ToolSpec(
        name="colab_write_file",
        description="Write text content to a file in the runtime's sandboxed workspace." + remote_note,
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "session_id": {"type": "string"},
            },
            "required": ["path", "content"],
        },
        handler=_write_file,
    ))
    registry.register(ToolSpec(
        name="colab_delete_file",
        description="Delete a file or directory (recursively) in the runtime's sandboxed workspace." + remote_note,
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}, "session_id": {"type": "string"}},
            "required": ["path"],
        },
        handler=_delete_file,
    ))
    registry.register(ToolSpec(
        name="colab_move_file",
        description="Move/rename a file within the runtime's sandboxed workspace." + remote_note,
        input_schema={
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "destination": {"type": "string"},
                "session_id": {"type": "string"},
            },
            "required": ["source", "destination"],
        },
        handler=_move_file,
    ))
    registry.register(ToolSpec(
        name="colab_create_directory",
        description="Create a directory (and parents) in the runtime's sandboxed workspace." + remote_note,
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}, "session_id": {"type": "string"}},
            "required": ["path"],
        },
        handler=_create_directory,
    ))
