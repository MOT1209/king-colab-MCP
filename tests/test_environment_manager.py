import pytest

from google_colab_mcp.utils.errors import PackageError, ValidationError


# The FakeRuntimeBackend used by `ctx` doesn't emulate pip's __PKG_RESULT__
# marker protocol, so these calls correctly surface PackageError — proving
# EnvironmentManager builds a snippet and routes it through execution
# rather than silently no-op-ing. Real pip behavior is covered by
# test_package_tools.py's validate_package_name unit tests and, for a real
# install, would need network access this suite intentionally avoids.


def test_install_package_reaches_pip_pipeline(ctx):
    with pytest.raises(PackageError):
        ctx.environment_manager.install_package("transformers")


def test_install_package_rejects_invalid_name(ctx):
    with pytest.raises(ValidationError):
        ctx.environment_manager.install_package("torch; rm -rf /")


def test_list_packages_reaches_pip_pipeline(ctx):
    with pytest.raises(PackageError):
        ctx.environment_manager.list_packages()


def test_save_and_list_profile_do_not_require_pip(ctx, monkeypatch):
    monkeypatch.setattr(ctx.environment_manager, "list_packages", lambda session_id=None: [{"name": "numpy", "version": "1.26.0"}])
    profile = ctx.environment_manager.save_profile("baseline")
    assert profile["name"] == "baseline"
    assert profile["packages"][0]["name"] == "numpy"
    assert "baseline" in ctx.environment_manager.list_profiles()


def test_get_missing_profile_raises(ctx):
    with pytest.raises(ValidationError):
        ctx.environment_manager.get_profile("does-not-exist")
