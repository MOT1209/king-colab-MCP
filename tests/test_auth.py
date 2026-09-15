from dataclasses import replace

import pytest

from google_colab_mcp.security.auth import authenticate
from google_colab_mcp.utils.errors import AuthenticationError


def test_no_auth_required_returns_anonymous(tmp_settings):
    principal = authenticate(tmp_settings, None)
    assert principal.id == "anonymous"


def test_api_key_mode_rejects_missing_token(tmp_settings):
    settings = replace(tmp_settings, require_auth=True, colab_auth_mode="api_key", mcp_auth_token="secret123")
    with pytest.raises(AuthenticationError):
        authenticate(settings, None)


def test_api_key_mode_rejects_wrong_token(tmp_settings):
    settings = replace(tmp_settings, require_auth=True, colab_auth_mode="api_key", mcp_auth_token="secret123")
    with pytest.raises(AuthenticationError):
        authenticate(settings, "wrong")


def test_api_key_mode_accepts_correct_token(tmp_settings):
    settings = replace(tmp_settings, require_auth=True, colab_auth_mode="api_key", mcp_auth_token="secret123")
    principal = authenticate(settings, "secret123")
    assert principal.auth_mode == "api_key"


def test_unsupported_auth_mode_raises(tmp_settings):
    settings = replace(tmp_settings, require_auth=True, colab_auth_mode="google_oauth")
    with pytest.raises(AuthenticationError):
        authenticate(settings, "anything")
