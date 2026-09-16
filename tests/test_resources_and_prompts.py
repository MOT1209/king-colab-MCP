import json

from google_colab_mcp.resources.resources import list_resources, read_resource
from google_colab_mcp.resources.prompts import PROMPT_DEFS, get_prompt


def test_list_resources_returns_expected_uris():
    uris = {r["uri"] for r in list_resources()}
    assert uris == {
        "colab://runtime",
        "colab://sessions",
        "colab://jobs",
        "colab://notebooks",
        "colab://artifacts",
        "colab://environments",
        "colab://datasets",
    }


def test_read_runtime_resource(ctx):
    payload = json.loads(read_resource(ctx, "colab://runtime"))
    assert "sessions" in payload


def test_read_jobs_resource(ctx):
    ctx.job_manager.submit("test", lambda j: 1)
    payload = json.loads(read_resource(ctx, "colab://jobs"))
    assert "jobs" in payload
    assert len(payload["jobs"]) >= 1


def test_read_unknown_resource_raises(ctx):
    import pytest

    with pytest.raises(KeyError):
        read_resource(ctx, "colab://nope")


def test_prompt_definitions_have_required_fields():
    for prompt in PROMPT_DEFS:
        assert prompt["name"]
        assert prompt["description"]


def test_get_prompt_content_renders_arguments():
    messages = get_prompt("run_with_gpu_if_available", {"code": "print(1)"})
    text = messages[0]["content"]["text"]
    assert "print(1)" in text
    assert "colab_get_gpu" in text
