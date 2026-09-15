"""Package management, executed as `pip` subprocess calls inside the runtime.

Every install/uninstall is written to the audit log by the server layer
(tools don't need to log directly), and package names are passed as
argv list elements to `subprocess.run` — never interpolated into a shell
string — so a malicious package name cannot break out into shell syntax.
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..context import ServerContext
from ..utils.errors import PackageError, ValidationError
from .registry import ToolRegistry, ToolSpec

_MARKER = "__PKG_RESULT__"
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9,._-]+\])?(==[A-Za-z0-9.*+!_-]+)?$")


def _validate_name(name: str) -> None:
    if not _NAME_RE.match(name):
        raise ValidationError(
            f"Invalid package specifier: {name!r}",
            suggestion="Use a plain PyPI package name, optionally with extras and/or a version pin, e.g. 'torch==2.3.0'.",
        )


def _run_pip(ctx: ServerContext, argv_tail: list[str], session_id: str | None, timeout: float) -> dict[str, Any]:
    snippet = f"""
import json, subprocess, sys
proc = subprocess.run([sys.executable, "-m", "pip", *{argv_tail!r}], capture_output=True, text=True)
print({_MARKER!r} + json.dumps({{"returncode": proc.returncode, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-4000:]}}))
"""
    out = ctx.execution_manager.run(snippet, session_id, timeout=timeout)
    for line in out["stdout"].splitlines():
        if line.startswith(_MARKER):
            return json.loads(line[len(_MARKER):])
    raise PackageError("pip did not report a result.", details=out["stdout"])


def _install_package(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    name = args["package"]
    _validate_name(name)
    result = _run_pip(ctx, ["install", "--quiet", name], args.get("session_id"), timeout=600)
    if result["returncode"] != 0:
        raise PackageError(f"pip install failed for '{name}'.", details=result["stderr"])
    return {"package": name, "installed": True, "log": result["stdout"]}


def _uninstall_package(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    name = args["package"]
    _validate_name(name)
    result = _run_pip(ctx, ["uninstall", "--yes", "--quiet", name], args.get("session_id"), timeout=300)
    if result["returncode"] != 0:
        raise PackageError(f"pip uninstall failed for '{name}'.", details=result["stderr"])
    return {"package": name, "uninstalled": True, "log": result["stdout"]}


def _list_packages(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    result = _run_pip(ctx, ["list", "--format", "json"], args.get("session_id"), timeout=60)
    if result["returncode"] != 0:
        raise PackageError("pip list failed.", details=result["stderr"])
    try:
        packages = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise PackageError("Could not parse pip list output.", details=str(exc)) from exc
    return {"packages": packages, "count": len(packages)}


def _get_package_version(ctx: ServerContext, args: dict[str, Any]) -> dict[str, Any]:
    name = args["package"]
    _validate_name(name)
    result = _run_pip(ctx, ["show", name], args.get("session_id"), timeout=30)
    if result["returncode"] != 0:
        raise PackageError(f"Package '{name}' is not installed.", details=result["stderr"])
    version = None
    for line in result["stdout"].splitlines():
        if line.lower().startswith("version:"):
            version = line.split(":", 1)[1].strip()
            break
    return {"package": name, "version": version}


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
