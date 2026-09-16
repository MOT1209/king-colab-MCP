from dataclasses import replace

import pytest

from google_colab_mcp.security.dangerous_tools import check_dangerous_tool_confirmed, is_dangerous
from google_colab_mcp.security.permissions import check_session_tool_permission
from google_colab_mcp.utils.errors import ApprovalRequiredError, AuthorizationError


def test_is_dangerous_flags_execution_and_destructive_tools():
    assert is_dangerous("colab_execute_code")
    assert is_dangerous("colab_delete_file")
    assert is_dangerous("colab_restart_runtime")
    assert not is_dangerous("colab_get_cpu")
    assert not is_dangerous("colab_list_jobs")


def test_confirm_not_required_by_default(tmp_settings):
    check_dangerous_tool_confirmed(tmp_settings, "colab_execute_code", {})


def test_confirm_required_when_enabled(tmp_settings):
    settings = replace(tmp_settings, dangerous_tools_require_confirm=True)
    with pytest.raises(ApprovalRequiredError):
        check_dangerous_tool_confirmed(settings, "colab_execute_code", {})
    check_dangerous_tool_confirmed(settings, "colab_execute_code", {"confirm": True})


def test_confirm_not_required_for_safe_tools(tmp_settings):
    settings = replace(tmp_settings, dangerous_tools_require_confirm=True)
    check_dangerous_tool_confirmed(settings, "colab_get_cpu", {})


def test_session_permission_denies_unlisted_tool(ctx):
    session = ctx.session_manager.create_session(provider_id="fake", permissions=["colab_get_cpu"])
    with pytest.raises(AuthorizationError):
        check_session_tool_permission(ctx.session_manager, "colab_execute_code", session.session_id)


def test_session_permission_allows_listed_tool(ctx):
    session = ctx.session_manager.create_session(provider_id="fake", permissions=["colab_execute_code"])
    check_session_tool_permission(ctx.session_manager, "colab_execute_code", session.session_id)


def test_session_without_permissions_list_is_unrestricted(ctx):
    session = ctx.session_manager.create_session(provider_id="fake")
    check_session_tool_permission(ctx.session_manager, "colab_execute_code", session.session_id)


def test_no_session_id_is_a_noop(ctx):
    check_session_tool_permission(ctx.session_manager, "colab_execute_code", None)
