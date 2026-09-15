"""File operations *inside the connected runtime* (e.g. Colab's /content).

Local file tools would only touch this machine, not the GPU/TPU runtime the
agent actually cares about. So every operation here is a small Python
snippet executed through `ExecutionManager` inside the target kernel,
confined to `remote_workspace_root` (default `/content/mcp_workspace`).
Binary content always travels as base64 so it survives the Jupyter message
protocol intact.
"""
from __future__ import annotations

import json
import posixpath
from typing import Any

from ..utils.errors import ExecutionError, PathAccessError
from .execution_manager import ExecutionManager

_MARKER = "__FS_RESULT__"


def _safe_join(root: str, relative_path: str) -> str:
    if not relative_path or relative_path.startswith("/") or ".." in relative_path.split("/"):
        raise PathAccessError(f"Unsafe remote path: {relative_path!r}")
    return posixpath.join(root, relative_path)


class RemoteFileManager:
    def __init__(self, execution_manager: ExecutionManager, root: str):
        self.execution_manager = execution_manager
        self.root = root

    def _run(self, snippet: str, session_id: str | None) -> dict[str, Any]:
        out = self.execution_manager.run(snippet, session_id, timeout=60)
        for line in out["stdout"].splitlines():
            if line.startswith(_MARKER):
                payload = json.loads(line[len(_MARKER):])
                if not payload.get("ok", True):
                    raise ExecutionError(payload.get("error", "remote filesystem operation failed"))
                return payload
        raise ExecutionError("Remote filesystem operation produced no result.", details=out["stdout"])

    def upload_file(self, path: str, content_b64: str, session_id: str | None = None) -> dict[str, Any]:
        target = _safe_join(self.root, path)
        snippet = f"""
import base64, json, os
os.makedirs(os.path.dirname({target!r}) or '.', exist_ok=True)
with open({target!r}, 'wb') as f:
    f.write(base64.b64decode({content_b64!r}))
print({_MARKER!r} + json.dumps({{"ok": True, "path": {target!r}, "size_bytes": os.path.getsize({target!r})}}))
"""
        return self._run(snippet, session_id)

    def download_file(self, path: str, session_id: str | None = None) -> dict[str, Any]:
        target = _safe_join(self.root, path)
        snippet = f"""
import base64, json, os
if not os.path.exists({target!r}):
    print({_MARKER!r} + json.dumps({{"ok": False, "error": "file not found: " + {target!r}}}))
else:
    with open({target!r}, 'rb') as f:
        data = f.read()
    print({_MARKER!r} + json.dumps({{"ok": True, "path": {target!r}, "content_b64": base64.b64encode(data).decode(), "size_bytes": len(data)}}))
"""
        return self._run(snippet, session_id)

    def read_file(self, path: str, session_id: str | None = None) -> dict[str, Any]:
        target = _safe_join(self.root, path)
        snippet = f"""
import json, os
if not os.path.exists({target!r}):
    print({_MARKER!r} + json.dumps({{"ok": False, "error": "file not found: " + {target!r}}}))
else:
    with open({target!r}, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    print({_MARKER!r} + json.dumps({{"ok": True, "path": {target!r}, "content": text}}))
"""
        return self._run(snippet, session_id)

    def write_file(self, path: str, content: str, session_id: str | None = None) -> dict[str, Any]:
        target = _safe_join(self.root, path)
        snippet = f"""
import json, os
os.makedirs(os.path.dirname({target!r}) or '.', exist_ok=True)
with open({target!r}, 'w', encoding='utf-8') as f:
    f.write({content!r})
print({_MARKER!r} + json.dumps({{"ok": True, "path": {target!r}}}))
"""
        return self._run(snippet, session_id)

    def list_files(self, path: str = "", session_id: str | None = None) -> dict[str, Any]:
        target = _safe_join(self.root, path) if path else self.root
        snippet = f"""
import json, os
base = {target!r}
os.makedirs(base, exist_ok=True)
entries = []
for name in sorted(os.listdir(base)):
    full = os.path.join(base, name)
    entries.append({{"name": name, "is_dir": os.path.isdir(full), "size_bytes": os.path.getsize(full) if os.path.isfile(full) else None}})
print({_MARKER!r} + json.dumps({{"ok": True, "path": base, "entries": entries}}))
"""
        return self._run(snippet, session_id)

    def delete_file(self, path: str, session_id: str | None = None) -> dict[str, Any]:
        target = _safe_join(self.root, path)
        snippet = f"""
import json, os, shutil
p = {target!r}
if os.path.isdir(p):
    shutil.rmtree(p)
elif os.path.exists(p):
    os.remove(p)
print({_MARKER!r} + json.dumps({{"ok": True, "path": p}}))
"""
        return self._run(snippet, session_id)

    def move_file(self, source: str, destination: str, session_id: str | None = None) -> dict[str, Any]:
        src = _safe_join(self.root, source)
        dst = _safe_join(self.root, destination)
        snippet = f"""
import json, os, shutil
os.makedirs(os.path.dirname({dst!r}) or '.', exist_ok=True)
shutil.move({src!r}, {dst!r})
print({_MARKER!r} + json.dumps({{"ok": True, "from": {src!r}, "to": {dst!r}}}))
"""
        return self._run(snippet, session_id)

    def create_directory(self, path: str, session_id: str | None = None) -> dict[str, Any]:
        target = _safe_join(self.root, path)
        snippet = f"""
import json, os
os.makedirs({target!r}, exist_ok=True)
print({_MARKER!r} + json.dumps({{"ok": True, "path": {target!r}}}))
"""
        return self._run(snippet, session_id)
