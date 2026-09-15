from google_colab_mcp.tools.registry import build_default_registry


def test_registry_has_no_duplicate_names():
    registry = build_default_registry()
    names = registry.names()
    assert len(names) == len(set(names))


def test_registry_covers_expected_core_tools():
    registry = build_default_registry()
    names = set(registry.names())
    expected = {
        "colab_execute_code",
        "colab_create_notebook",
        "colab_get_notebook",
        "colab_execute_notebook",
        "colab_get_runtime",
        "colab_get_gpu",
        "colab_install_package",
        "colab_list_packages",
        "colab_upload_file",
        "colab_download_file",
        "colab_list_files",
        "colab_get_job",
        "colab_cancel_job",
        "colab_get_logs",
        "colab_get_artifacts",
        "colab_run_training",
    }
    missing = expected - names
    assert not missing, f"missing tools: {missing}"


def test_every_tool_has_valid_schema():
    registry = build_default_registry()
    for spec in registry.all():
        assert spec.input_schema.get("type") == "object"
        assert spec.description
        assert callable(spec.handler)
