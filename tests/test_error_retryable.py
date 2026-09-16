from google_colab_mcp.utils.errors import (
    AuthenticationError,
    AuthorizationError,
    ColabUnavailableError,
    ExecutionTimeoutError,
    NetworkError,
    ProviderError,
    RateLimitError,
    ResourceExhaustedError,
    RuntimeUnavailableError,
    ValidationError,
)


def test_user_errors_are_not_retryable():
    assert ValidationError("bad").to_dict()["error"]["retryable"] is False
    assert AuthenticationError("bad").to_dict()["error"]["retryable"] is False
    assert AuthorizationError("bad").to_dict()["error"]["retryable"] is False


def test_transient_errors_are_retryable():
    assert RuntimeUnavailableError("gone").to_dict()["error"]["retryable"] is True
    assert NetworkError("blip").to_dict()["error"]["retryable"] is True
    assert ProviderError("down").to_dict()["error"]["retryable"] is True
    assert ColabUnavailableError("no colab").to_dict()["error"]["retryable"] is True
    assert ExecutionTimeoutError("slow").to_dict()["error"]["retryable"] is True
    assert RateLimitError("slow down").to_dict()["error"]["retryable"] is True
    assert ResourceExhaustedError("too big").to_dict()["error"]["retryable"] is True


def test_retryable_can_be_overridden_per_instance():
    err = ValidationError("bad", retryable=True)
    assert err.to_dict()["error"]["retryable"] is True
