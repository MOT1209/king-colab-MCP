from dataclasses import replace

import pytest

from google_colab_mcp.security.permissions import check_tool_permission
from google_colab_mcp.utils.errors import AuthorizationError


def test_allows_when_no_lists_configured(tmp_settings):
    check_tool_permission(tmp_settings, "colab_execute_code")


def test_denied_tool_raises(tmp_settings):
    settings = replace(tmp_settings, denied_tools=["colab_execute_code"])
    with pytest.raises(AuthorizationError):
        check_tool_permission(settings, "colab_execute_code")


def test_allowlist_blocks_unlisted_tool(tmp_settings):
    settings = replace(tmp_settings, allowed_tools=["colab_get_runtime"])
    with pytest.raises(AuthorizationError):
        check_tool_permission(settings, "colab_execute_code")


def test_allowlist_permits_listed_tool(tmp_settings):
    settings = replace(tmp_settings, allowed_tools=["colab_get_runtime"])
    check_tool_permission(settings, "colab_get_runtime")
