"""Runtime / hardware introspection.

Every "get_X_info" tool works the same way: run a small, self-contained
Python snippet in the target kernel that gathers facts and prints them as
JSON, then parse that JSON back here. This keeps the MCP server itself
free of any hard dependency on torch/psutil/pynvml — those only need to be
importable *inside the runtime being inspected*, and each snippet degrades
gracefully (reports availability=false) when a library is missing there.
"""
from __future__ import annotations

import json
from typing import Any

from .execution_manager import ExecutionManager

_RUNTIME_INFO_SNIPPET = """
import json, sys, platform
info = {"python_version": sys.version, "platform": platform.platform()}
try:
    import torch
    info["cuda_available"] = torch.cuda.is_available()
    info["cuda_version"] = torch.version.cuda
    info["torch_version"] = torch.__version__
except Exception:
    info["cuda_available"] = False
try:
    import pkg_resources
    info["installed_package_count"] = len(list(pkg_resources.working_set))
except Exception:
    pass
print("__RUNTIME_INFO__" + json.dumps(info))
"""

_GPU_INFO_SNIPPET = """
import json
info = {"available": False, "devices": []}
try:
    import torch
    if torch.cuda.is_available():
        info["available"] = True
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            info["devices"].append({
                "index": i,
                "name": props.name,
                "total_memory_mb": round(props.total_memory / (1024 * 1024), 1),
                "multi_processor_count": props.multi_processor_count,
            })
except Exception as exc:
    info["error"] = str(exc)
print("__GPU_INFO__" + json.dumps(info))
"""

_CPU_INFO_SNIPPET = """
import json, os
info = {"logical_cores": os.cpu_count()}
try:
    import psutil
    info["physical_cores"] = psutil.cpu_count(logical=False)
    info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
except Exception:
    pass
print("__CPU_INFO__" + json.dumps(info))
"""

_MEMORY_INFO_SNIPPET = """
import json
info = {}
try:
    import psutil
    vm = psutil.virtual_memory()
    info = {"total_mb": round(vm.total / (1024 * 1024), 1),
            "available_mb": round(vm.available / (1024 * 1024), 1),
            "percent_used": vm.percent}
except Exception as exc:
    info = {"error": str(exc)}
print("__MEMORY_INFO__" + json.dumps(info))
"""

_DISK_INFO_SNIPPET = """
import json, shutil
info = {}
try:
    usage = shutil.disk_usage("/")
    info = {"total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2)}
except Exception as exc:
    info = {"error": str(exc)}
print("__DISK_INFO__" + json.dumps(info))
"""


def _extract(stdout: str, marker: str) -> dict[str, Any]:
    for line in stdout.splitlines():
        if line.startswith(marker):
            return json.loads(line[len(marker):])
    return {}


class RuntimeManager:
    def __init__(self, execution_manager: ExecutionManager):
        self.execution_manager = execution_manager

    def get_runtime_info(self, session_id: str | None = None) -> dict[str, Any]:
        out = self.execution_manager.run(_RUNTIME_INFO_SNIPPET, session_id, timeout=30)
        return _extract(out["stdout"], "__RUNTIME_INFO__")

    def get_gpu_info(self, session_id: str | None = None) -> dict[str, Any]:
        out = self.execution_manager.run(_GPU_INFO_SNIPPET, session_id, timeout=30)
        return _extract(out["stdout"], "__GPU_INFO__")

    def get_cpu_info(self, session_id: str | None = None) -> dict[str, Any]:
        out = self.execution_manager.run(_CPU_INFO_SNIPPET, session_id, timeout=30)
        return _extract(out["stdout"], "__CPU_INFO__")

    def get_memory_info(self, session_id: str | None = None) -> dict[str, Any]:
        out = self.execution_manager.run(_MEMORY_INFO_SNIPPET, session_id, timeout=30)
        return _extract(out["stdout"], "__MEMORY_INFO__")

    def get_disk_info(self, session_id: str | None = None) -> dict[str, Any]:
        out = self.execution_manager.run(_DISK_INFO_SNIPPET, session_id, timeout=30)
        return _extract(out["stdout"], "__DISK_INFO__")
