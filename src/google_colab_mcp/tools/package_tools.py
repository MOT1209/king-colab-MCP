"""Thin MCP wrappers around `colab/environment_manager.py::EnvironmentManager`.

No pip/subprocess logic lives here — see EnvironmentManager for that, and
for `validate_package_name`'s argv-safety guarantees (package names are
never interpolated into a shell string).
"""
from __future__ import annotations

from typing import Any

from ..context import ServerContext
from .registry import ToolRegistry, ToolSpec


def _install_package(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.environment_manager.install_package(args["package"], args.get("session_id"))


def _uninstall_package(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.environment_manager.remove_package(args["package"], args.get("session_id"))


def _list_packages(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    packages = ctx.environment_manager.list_packages(args.get("session_id"))
    return {"packages": packages, "count": len(packages)}


def _get_package_version(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    version = ctx.environment_manager.get_package_version(args["package"], args.get("session_id"))
    return {"package": args["package"], "version": version}


def _export_requirements(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return {"requirements_txt": ctx.environment_manager.export_requirements(args.get("session_id"))}


def _install_requirements(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.environment_manager.install_requirements(args["requirements_txt"], args.get("session_id"))


def _save_environment_profile(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.environment_manager.save_profile(args["name"], args.get("session_id"))


def _apply_environment_profile(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return ctx.environment_manager.apply_profile(args["name"], args.get("session_id"))


def _list_environment_profiles(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    return {"profiles": ctx.environment_manager.list_profiles()}


def register(registry: ToolRegistry) -> None:
    registry.register(ToolSpec(
        name="colab_install_package",
        description="Install a Python package (e.g. 'transformers', 'torch==2.3.0') inside the runtime via pip.",
        input_schema={
            "type": "object",
            "properties": {"package": {"type": "string"}, "session_id": {"type": "string"}},
            "required": ["package"],
        },
        handler=_install_package,
    ))
    registry.register(ToolSpec(
        name="colab_uninstall_package",
        description="Uninstall a Python package from the runtime via pip.",
        input_schema={
            "type": "object",
            "properties": {"package": {"type": "string"}, "session_id": {"type": "string"}},
            "required": ["package"],
        },
        handler=_uninstall_package,
    ))
    registry.register(ToolSpec(
        name="colab_list_packages",
        description="List all installed packages and their versions in the runtime.",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}},
        handler=_list_packages,
    ))
    registry.register(ToolSpec(
        name="colab_get_package_version",
        description="Get the installed version of a specific package in the runtime.",
        input_schema={
            "type": "object",
            "properties": {"package": {"type": "string"}, "session_id": {"type": "string"}},
            "required": ["package"],
        },
        handler=_get_package_version,
    ))
    registry.register(ToolSpec(
        name="colab_export_requirements",
        description="Export the runtime's installed packages as a requirements.txt-formatted string (pip freeze).",
        input_schema={"type": "object", "properties": {"session_id": {"type": "string"}}},
        handler=_export_requirements,
    ))
    registry.register(ToolSpec(
        name="colab_install_requirements",
        description="Install every package listed in a requirements.txt-formatted string.",
        input_schema={
            "type": "object",
            "properties": {"requirements_txt": {"type": "string"}, "session_id": {"type": "string"}},
            "required": ["requirements_txt"],
        },
        handler=_install_requirements,
    ))
    registry.register(ToolSpec(
        name="colab_save_environment_profile",
        description="Snapshot the runtime's currently installed packages as a named, reusable EnvironmentProfile.",
        input_schema={
            "type": "object",
            "properties": {"name": {"type": "string"}, "session_id": {"type": "string"}},
            "required": ["name"],
        },
        handler=_save_environment_profile,
    ))
    registry.register(ToolSpec(
        name="colab_apply_environment_profile",
        description="Install every package recorded in a previously saved EnvironmentProfile.",
        input_schema={
            "type": "object",
            "properties": {"name": {"type": "string"}, "session_id": {"type": "string"}},
            "required": ["name"],
        },
        handler=_apply_environment_profile,
    ))
    registry.register(ToolSpec(
        name="colab_list_environment_profiles",
        description="List saved EnvironmentProfile names.",
        input_schema={"type": "object", "properties": {}},
        handler=_list_environment_profiles,
    ))
