from google_colab_mcp.utils.errors import ExecutionError, ValidationError


def test_error_to_dict_shape():
    err = ExecutionError("something failed", details="traceback here")
    payload = err.to_dict()
    assert payload["success"] is False
    assert payload["error"]["type"] == "execution_error"
    assert payload["error"]["message"] == "something failed"
    assert payload["error"]["details"] == "traceback here"
    assert "suggestion" in payload["error"]


def test_error_defaults_details_to_message():
    err = ValidationError("bad input")
    assert err.to_dict()["error"]["details"] == "bad input"


def test_custom_suggestion_overrides_default():
    err = ValidationError("bad input", suggestion="try again")
    assert err.to_dict()["error"]["suggestion"] == "try again"
