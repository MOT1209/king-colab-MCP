import pytest

from google_colab_mcp.colab.environment_manager import validate_package_name
from google_colab_mcp.utils.errors import ValidationError


def test_validate_name_accepts_plain_package():
    validate_package_name("transformers")


def test_validate_name_accepts_version_pin():
    validate_package_name("torch==2.3.0")


def test_validate_name_accepts_extras():
    validate_package_name("uvicorn[standard]")


def test_validate_name_rejects_shell_injection_attempt():
    with pytest.raises(ValidationError):
        validate_package_name("torch; rm -rf /")


def test_validate_name_rejects_flag_injection():
    with pytest.raises(ValidationError):
        validate_package_name("--index-url=http://evil.example")
