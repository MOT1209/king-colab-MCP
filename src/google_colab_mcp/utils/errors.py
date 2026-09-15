"""Structured error types returned to MCP clients.

Every tool failure surfaces as JSON shaped like:

    {
      "success": false,
      "error": {
        "type": "...",
        "message": "...",
        "details": "...",
        "suggestion": "..."
      }
    }

Real exception text is always preserved in `details` — never swallowed.
"""
from __future__ import annotations

from typing import Any


class ColabMCPError(Exception):
    """Base class for all structured, user-facing errors raised by this server."""

    error_type = "internal_error"
    suggestion = "Check server logs for details."

    def __init__(self, message: str, details: str | None = None, suggestion: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or message
        if suggestion:
            self.suggestion = suggestion

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": False,
            "error": {
                "type": self.error_type,
                "message": self.message,
                "details": self.details,
                "suggestion": self.suggestion,
            },
        }


class AuthenticationError(ColabMCPError):
    error_type = "authentication_error"
    suggestion = "Verify your MCP auth token / credentials are set and not expired."


class AuthorizationError(ColabMCPError):
    error_type = "authorization_error"
    suggestion = "This tool or path is not permitted for the current principal. Check tool permissions."


class ValidationError(ColabMCPError):
    error_type = "validation_error"
    suggestion = "Check the arguments passed to the tool against its schema."


class PathAccessError(ColabMCPError):
    error_type = "path_access_error"
    suggestion = "Only paths inside the configured workspace root are accessible."


class RateLimitError(ColabMCPError):
    error_type = "rate_limit_error"
    suggestion = "Slow down requests or raise MAX_REQUESTS_PER_MINUTE."


class RuntimeUnavailableError(ColabMCPError):
    error_type = "runtime_unavailable_error"
    suggestion = "No active Colab/Jupyter runtime is connected. Call colab_get_runtime or reconnect the kernel."


class ExecutionError(ColabMCPError):
    error_type = "execution_error"
    suggestion = "Inspect the traceback in 'details' for the failing Python code."


class ExecutionTimeoutError(ColabMCPError):
    error_type = "timeout_error"
    suggestion = "Increase the tool's timeout_seconds or optimize the code."


class PackageError(ColabMCPError):
    error_type = "package_error"
    suggestion = "Verify the package name and that the runtime has network/pip access."


class NotebookError(ColabMCPError):
    error_type = "notebook_error"
    suggestion = "Verify the notebook path exists and is valid .ipynb JSON."


class JobNotFoundError(ColabMCPError):
    error_type = "job_not_found_error"
    suggestion = "Check the job_id with colab_get_job or list active jobs via the colab://jobs resource."


class ConnectionError_(ColabMCPError):
    error_type = "connection_error"
    suggestion = "Verify the runtime/kernel gateway is reachable and connection info is correct."
