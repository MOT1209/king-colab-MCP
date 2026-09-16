"""Structured error types returned to MCP clients.

Every tool failure surfaces as JSON shaped like:

    {
      "success": false,
      "error": {
        "type": "...",
        "message": "...",
        "details": "...",
        "suggestion": "...",
        "retryable": true
      }
    }

Real exception text is always preserved in `details` — never swallowed.
`retryable` tells a caller whether re-issuing the same call could plausibly
succeed (a transient network blip, a busy execution slot) versus won't
(a validation error, an authorization denial) without it string-matching
`error.type`.
"""
from __future__ import annotations

from typing import Any


class ColabMCPError(Exception):
    """Base class for all structured, user-facing errors raised by this server."""

    error_type = "internal_error"
    suggestion = "Check server logs for details."
    retryable = False

    def __init__(
        self,
        message: str,
        details: str | None = None,
        suggestion: str | None = None,
        retryable: bool | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or message
        if suggestion:
            self.suggestion = suggestion
        if retryable is not None:
            self.retryable = retryable

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": False,
            "error": {
                "type": self.error_type,
                "message": self.message,
                "details": self.details,
                "suggestion": self.suggestion,
                "retryable": self.retryable,
            },
        }


# --- User errors: the caller must change something before retrying -------

class ValidationError(ColabMCPError):
    error_type = "validation_error"
    suggestion = "Check the arguments passed to the tool against its schema."
    retryable = False


class PathAccessError(ColabMCPError):
    error_type = "path_access_error"
    suggestion = "Only paths inside the configured workspace root are accessible."
    retryable = False


class NotebookError(ColabMCPError):
    error_type = "notebook_error"
    suggestion = "Verify the notebook path exists and is valid .ipynb JSON."
    retryable = False


class JobNotFoundError(ColabMCPError):
    error_type = "job_not_found_error"
    suggestion = "Check the job_id with colab_get_job or list active jobs via the colab://jobs resource."
    retryable = False


# --- Authentication / authorization ---------------------------------------

class AuthenticationError(ColabMCPError):
    error_type = "authentication_error"
    suggestion = "Verify your MCP auth token / credentials are set and not expired."
    retryable = False


class AuthorizationError(ColabMCPError):
    error_type = "authorization_error"
    suggestion = "This tool or path is not permitted for the current principal. Check tool permissions."
    retryable = False


class ApprovalRequiredError(ColabMCPError):
    """Raised when a dangerous tool is called without the required explicit approval flag."""

    error_type = "approval_required_error"
    suggestion = "Re-call this tool with 'confirm: true' (or have an operator approve it) — it is marked dangerous."
    retryable = False


# --- Runtime / provider errors --------------------------------------------

class RuntimeUnavailableError(ColabMCPError):
    error_type = "runtime_unavailable_error"
    suggestion = "No active runtime is connected. Call colab_get_runtime or create/reconnect a session."
    retryable = True


class ProviderError(ColabMCPError):
    """A RuntimeProvider-level failure (discovery, provider-specific auth, provider health check)."""

    error_type = "provider_error"
    suggestion = "Check the provider's specific requirements (see docs/RUNTIME_PROVIDERS.md)."
    retryable = True


class ColabUnavailableError(ProviderError):
    """Raised when a caller asked specifically for Google Colab but no real Colab runtime is reachable.

    Never silently falls back to treating a generic Jupyter kernel as Colab.
    """

    error_type = "colab_unavailable_error"
    suggestion = (
        "No real Google Colab runtime is connected — this server will not silently treat a "
        "generic Jupyter kernel as Colab. See docs/COLAB.md for how to attach one."
    )
    retryable = True


class NetworkError(ColabMCPError):
    error_type = "network_error"
    suggestion = "Check network connectivity between this server and the runtime/provider."
    retryable = True


class ConnectionError_(NetworkError):
    error_type = "connection_error"
    suggestion = "Verify the runtime/kernel gateway is reachable and connection info is correct."
    retryable = True


# --- Execution errors -------------------------------------------------

class ExecutionError(ColabMCPError):
    error_type = "execution_error"
    suggestion = "Inspect the traceback in 'details' for the failing Python code."
    retryable = False


class ExecutionTimeoutError(ColabMCPError):
    error_type = "timeout_error"
    suggestion = "Increase the tool's timeout_seconds or optimize the code."
    retryable = True


class PackageError(ColabMCPError):
    error_type = "package_error"
    suggestion = "Verify the package name and that the runtime has network/pip access."
    retryable = False


class DatasetError(ColabMCPError):
    error_type = "dataset_error"
    suggestion = "Verify the dataset source/path and that any required credentials are configured."
    retryable = False


# --- Resource / rate limiting ------------------------------------------

class RateLimitError(ColabMCPError):
    error_type = "rate_limit_error"
    suggestion = "Slow down requests or raise MAX_REQUESTS_PER_MINUTE."
    retryable = True


class ResourceExhaustedError(ColabMCPError):
    """Output/file size limits, concurrent job quotas, disk quotas, etc."""

    error_type = "resource_exhausted_error"
    suggestion = "Reduce output/file size or wait for other jobs/sessions to free resources."
    retryable = True
