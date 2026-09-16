"""Package/environment management: the single place that knows how to
drive `pip` inside a runtime session, plus save/restore of named
`EnvironmentProfile`s (a snapshot of installed packages a session can be
rebuilt from later).

`tools/package_tools.py` and `tools/runtime_tools.py` are thin wrappers
around this class — they hold no pip logic of their own.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from ..security.path_guard import PathGuard
from ..utils.errors import PackageError, ValidationError
from .execution_manager import ExecutionManager

_MARKER = "__PKG_RESULT__"
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9,._-]+\])?(==[A-Za-z0-9.*+!_-]+)?$")


def validate_package_name(name: str) -> None:
    if not _NAME_RE.match(name):
        raise ValidationError(
            f"Invalid package specifier: {name!r}",
            suggestion="Use a plain PyPI package name, optionally with extras and/or a version pin, e.g. 'torch==2.3.0'.",
        )


class EnvironmentManager:
    def __init__(self, execution_manager: ExecutionManager, profile_guard: PathGuard):
        self.execution_manager = execution_manager
        self.profile_guard = profile_guard
        self._profiles_index = self.profile_guard.root / "_profiles.json"
        if not self._profiles_index.exists():
            self._profiles_index.write_text("{}")

    def _run_pip(self, argv_tail: list[str], session_id: str | None, timeout: float) -> dict[str, Any]:
        snippet = f"""
import json, subprocess, sys
proc = subprocess.run([sys.executable, "-m", "pip", *{argv_tail!r}], capture_output=True, text=True)
print({_MARKER!r} + json.dumps({{"returncode": proc.returncode, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-4000:]}}))
"""
        out = self.execution_manager.run(snippet, session_id, timeout=timeout)
        for line in out["stdout"].splitlines():
            if line.startswith(_MARKER):
                return json.loads(line[len(_MARKER):])
        raise PackageError("pip did not report a result.", details=out["stdout"])

    def install_package(self, name: str, session_id: str | None = None) -> dict[str, Any]:
        validate_package_name(name)
        result = self._run_pip(["install", "--quiet", name], session_id, timeout=600)
        if result["returncode"] != 0:
            raise PackageError(f"pip install failed for '{name}'.", details=result["stderr"])
        return {"package": name, "installed": True, "log": result["stdout"]}

    def remove_package(self, name: str, session_id: str | None = None) -> dict[str, Any]:
        validate_package_name(name)
        result = self._run_pip(["uninstall", "--yes", "--quiet", name], session_id, timeout=300)
        if result["returncode"] != 0:
            raise PackageError(f"pip uninstall failed for '{name}'.", details=result["stderr"])
        return {"package": name, "removed": True, "log": result["stdout"]}

    def list_packages(self, session_id: str | None = None) -> list[dict[str, str]]:
        result = self._run_pip(["list", "--format", "json"], session_id, timeout=60)
        if result["returncode"] != 0:
            raise PackageError("pip list failed.", details=result["stderr"])
        try:
            return json.loads(result["stdout"])
        except json.JSONDecodeError as exc:
            raise PackageError("Could not parse pip list output.", details=str(exc)) from exc

    def get_package_version(self, name: str, session_id: str | None = None) -> str | None:
        validate_package_name(name)
        result = self._run_pip(["show", name], session_id, timeout=30)
        if result["returncode"] != 0:
            raise PackageError(f"Package '{name}' is not installed.", details=result["stderr"])
        for line in result["stdout"].splitlines():
            if line.lower().startswith("version:"):
                return line.split(":", 1)[1].strip()
        return None

    def export_requirements(self, session_id: str | None = None) -> str:
        result = self._run_pip(["freeze"], session_id, timeout=60)
        if result["returncode"] != 0:
            raise PackageError("pip freeze failed.", details=result["stderr"])
        return result["stdout"]

    def install_requirements(self, requirements_text: str, session_id: str | None = None) -> dict[str, Any]:
        for line in requirements_text.splitlines():
            spec = line.strip()
            if not spec or spec.startswith("#"):
                continue
            validate_package_name(spec)
        target = self.profile_guard.root / f"_req_{int(time.time() * 1000)}.txt"
        target.write_text(requirements_text)
        try:
            snippet = f"""
import json, subprocess, sys
proc = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "-r", {str(target)!r}], capture_output=True, text=True)
print({_MARKER!r} + json.dumps({{"returncode": proc.returncode, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-4000:]}}))
"""
            out = self.execution_manager.run(snippet, session_id, timeout=900)
            for line in out["stdout"].splitlines():
                if line.startswith(_MARKER):
                    result = json.loads(line[len(_MARKER):])
                    if result["returncode"] != 0:
                        raise PackageError("pip install -r requirements failed.", details=result["stderr"])
                    return {"installed": True, "log": result["stdout"]}
            raise PackageError("pip did not report a result for requirements install.")
        finally:
            target.unlink(missing_ok=True)

    # --- Environment profiles -------------------------------------------

    def save_profile(self, name: str, session_id: str | None = None) -> dict[str, Any]:
        packages = self.list_packages(session_id)
        profile = {"name": name, "packages": packages, "saved_at": time.time()}
        index = json.loads(self._profiles_index.read_text())
        index[name] = profile
        self._profiles_index.write_text(json.dumps(index, indent=2))
        return profile

    def get_profile(self, name: str) -> dict[str, Any]:
        index = json.loads(self._profiles_index.read_text())
        if name not in index:
            raise ValidationError(f"No such environment profile: {name}")
        return index[name]

    def list_profiles(self) -> list[str]:
        return list(json.loads(self._profiles_index.read_text()).keys())

    def apply_profile(self, name: str, session_id: str | None = None) -> dict[str, Any]:
        profile = self.get_profile(name)
        requirements = "\n".join(f"{p['name']}=={p['version']}" for p in profile["packages"])
        return self.install_requirements(requirements, session_id)
