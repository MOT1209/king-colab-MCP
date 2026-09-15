from google_colab_mcp.security.redact import redact_secrets


def test_redacts_key_value_pairs():
    text = "api_key=sk-abcdefghijklmnopqrstuvwxyz1234567890"
    out = redact_secrets(text)
    assert "sk-abcdefghijklmnopqrstuvwxyz1234567890" not in out
    assert "[REDACTED]" in out


def test_redacts_google_api_key_pattern():
    text = "found key AIzaSyD-1234567890abcdefghijklmnopqrstuv in logs"
    out = redact_secrets(text)
    assert "AIzaSyD" not in out


def test_redacts_github_token_pattern():
    text = "token: ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    out = redact_secrets(text)
    assert "ghp_abcdefghijklmnopqrstuvwxyz0123456789" not in out


def test_leaves_normal_text_untouched():
    text = "hello world, this is a normal log line with no secrets"
    assert redact_secrets(text) == text


def test_handles_empty_string():
    assert redact_secrets("") == ""
