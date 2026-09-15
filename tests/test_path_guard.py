import pytest

from google_colab_mcp.security.path_guard import PathGuard
from google_colab_mcp.utils.errors import PathAccessError


def test_resolve_valid_relative_path(tmp_path):
    guard = PathGuard(tmp_path)
    resolved = guard.resolve("subdir/file.txt")
    assert resolved == (tmp_path / "subdir" / "file.txt").resolve()


def test_resolve_rejects_parent_traversal(tmp_path):
    guard = PathGuard(tmp_path)
    with pytest.raises(PathAccessError):
        guard.resolve("../../etc/passwd")


def test_resolve_rejects_absolute_escape(tmp_path):
    guard = PathGuard(tmp_path)
    with pytest.raises(PathAccessError):
        guard.resolve("/etc/passwd")


def test_resolve_allows_nested_valid_path(tmp_path):
    guard = PathGuard(tmp_path)
    resolved = guard.resolve("a/b/c.ipynb")
    assert str(resolved).startswith(str(tmp_path.resolve()))
