"""Confines all file-tool access to a configured workspace root.

Prevents path traversal (`../../etc/passwd`), absolute-path escapes, and
symlink escapes out of the sandboxed workspace directory.
"""
from __future__ import annotations

from pathlib import Path

from ..utils.errors import PathAccessError


class PathGuard:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str) -> Path:
        """Resolve a user-supplied path against the workspace root, rejecting escapes."""
        if relative_path is None:
            raise PathAccessError("Path must not be empty.")

        candidate = (self.root / relative_path).resolve()

        try:
            candidate.relative_to(self.root)
        except ValueError:
            raise PathAccessError(
                f"Path '{relative_path}' resolves outside the workspace root.",
                details=f"resolved={candidate} root={self.root}",
            )
        return candidate
