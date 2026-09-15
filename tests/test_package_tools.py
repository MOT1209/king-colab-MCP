import pytest

from google_colab_mcp.tools.package_tools import _validate_name
from google_colab_mcp.utils.errors import ValidationError


def test_validate_name_accepts_plain_package():
    _validate_name("transformers")


def test_validate_name_accepts_version_pin():
    _validate_name("torch==2.3.0")


def test_validate_name_accepts_extras():
    _validate_name("uvicorn[standard]")


def test_validate_name_rejects_shell_injection_attempt():
    with pytest.raises(ValidationError):
        _validate_name("torch; rm -rf /")


def test_validate_name_rejects_flag_injection():
    with pytest.raises(ValidationError):
        _validate_name("--index-url=http://evil.example")
