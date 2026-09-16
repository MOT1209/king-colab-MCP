"""Dangerous-tool policy.

Every tool that executes arbitrary code, mutates the runtime's environment,
or is destructive is listed here. When `DANGEROUS_TOOLS_REQUIRE_CONFIRM=true`,
calling one of these without `"confirm": true` in the arguments is refused
with `ApprovalRequiredError` — cheap insurance against an agent calling
`colab_delete_file` or `colab_restart_runtime` on autopilot.
"""
from __future__ import annotations

from typing import Any

from ..config import Settings
from ..utils.errors import ApprovalRequiredError

DANGEROUS_TOOLS: frozenset[str] = frozenset({
    "colab_execute_code",
    "colab_execute_cell",
    "colab_execute_notebook",
    "colab_install_package",
    "colab_uninstall_package",
    "colab_install_requirements",
    "colab_delete_file",
    "colab_delete_cell",
    "colab_move_file",
    "colab_restart_runtime",
    "colab_close_session",
    "colab_run_training",
    "colab_save_model",
    "colab_export_model",
    "colab_cache_dataset_from_url",
})


def is_dangerous(tool_name: str) -> bool:
    return tool_name in DANGEROUS_TOOLS


def check_dangerous_tool_confirmed(settings: Settings, tool_name: str, arguments: dict[str, Any]) -> None:
    if not settings.dangerous_tools_require_confirm:
        return
    if not is_dangerous(tool_name):
        return
    if arguments.get("confirm") is not True:
        raise ApprovalRequiredError(
            f"'{tool_name}' is marked dangerous and DANGEROUS_TOOLS_REQUIRE_CONFIRM is enabled.",
        )
