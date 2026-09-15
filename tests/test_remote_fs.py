import pytest

from google_colab_mcp.colab.remote_fs import _safe_join
from google_colab_mcp.utils.errors import PathAccessError


def test_safe_join_allows_relative_path():
    assert _safe_join("/content/mcp_workspace", "a/b.txt") == "/content/mcp_workspace/a/b.txt"


def test_safe_join_rejects_parent_traversal():
    with pytest.raises(PathAccessError):
        _safe_join("/content/mcp_workspace", "../etc/passwd")


def test_safe_join_rejects_absolute_path():
    with pytest.raises(PathAccessError):
        _safe_join("/content/mcp_workspace", "/etc/passwd")


def test_safe_join_rejects_empty_path():
    with pytest.raises(PathAccessError):
        _safe_join("/content/mcp_workspace", "")
