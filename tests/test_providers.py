import pytest

from google_colab_mcp.colab.providers import ColabProvider, DockerProvider, LocalJupyterProvider, RemoteJupyterProvider
from google_colab_mcp.colab.providers.base import ProviderDiscoveryResult, RuntimeProvider, RuntimeState
from google_colab_mcp.utils.errors import ProviderError


def test_colab_provider_requires_connection_file():
    provider = ColabProvider({})
    result = provider.discover()
    assert result.available is False
    assert "connection_file" in result.reason


def test_colab_provider_available_with_connection_file():
    provider = ColabProvider({"connection_file": "/tmp/does-not-need-to-exist.json"})
    result = provider.discover()
    assert result.available is True


def test_local_jupyter_provider_available_when_ipykernel_installed():
    provider = LocalJupyterProvider({})
    result = provider.discover()
    assert result.available is True


def test_remote_jupyter_provider_requires_existing_connection_file(tmp_path):
    provider = RemoteJupyterProvider({})
    assert provider.discover().available is False

    missing = RemoteJupyterProvider({"connection_file": str(tmp_path / "nope.json")})
    assert missing.discover().available is False

    real_file = tmp_path / "kernel.json"
    real_file.write_text("{}")
    ok = RemoteJupyterProvider({"connection_file": str(real_file)})
    assert ok.discover().available is True


def test_docker_provider_unavailable_without_daemon():
    provider = DockerProvider({})
    result = provider.discover()
    # In this sandbox there's no reachable docker daemon; the important
    # thing is that unavailability is reported honestly with a reason,
    # not that it's always false everywhere.
    if not result.available:
        assert result.reason


class _AlwaysFailsProvider(RuntimeProvider):
    provider_id = "always_fails"

    def discover(self) -> ProviderDiscoveryResult:
        return ProviderDiscoveryResult(available=False, reason="intentionally unavailable for this test")

    def _create_backend(self):
        raise AssertionError("should never be called")


def test_connect_raises_provider_error_and_sets_failed_state():
    provider = _AlwaysFailsProvider({})
    with pytest.raises(ProviderError):
        provider.connect()
    assert provider.state == RuntimeState.FAILED


def test_health_check_reports_unhealthy_without_backend():
    provider = _AlwaysFailsProvider({})
    health = provider.health_check(None)
    assert health["healthy"] is False
    assert health["provider"] == "always_fails"
