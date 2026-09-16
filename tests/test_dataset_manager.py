import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from google_colab_mcp.colab.dataset_manager import DatasetManager, SOURCE_CONNECTORS
from google_colab_mcp.security.path_guard import PathGuard
from google_colab_mcp.utils.errors import DatasetError, ResourceExhaustedError


@pytest.fixture
def dm(tmp_path):
    return DatasetManager(PathGuard(tmp_path), max_download_bytes=1_000_000)


def test_upload_register_and_download_roundtrip(dm):
    content = b"col1,col2\n1,2\n3,4\n"
    entry = dm.upload("my_csv", "data/my.csv", base64.b64encode(content).decode())
    assert entry["version"] == 1
    assert entry["size_bytes"] == len(content)

    downloaded = dm.download("my_csv")
    assert base64.b64decode(downloaded["content_base64"]) == content


def test_upload_over_size_limit_rejected(tmp_path):
    small_dm = DatasetManager(PathGuard(tmp_path), max_download_bytes=10)
    content = b"x" * 100
    with pytest.raises(ResourceExhaustedError):
        small_dm.upload("big", "big.bin", base64.b64encode(content).decode())


def test_validate_detects_tampering(dm):
    dm.upload("ds", "ds.txt", base64.b64encode(b"original").decode())
    resolved = dm.path_guard.resolve("ds.txt")
    resolved.write_bytes(b"tampered!")
    result = dm.validate("ds")
    assert result["valid"] is False


def test_validate_passes_for_unmodified_file(dm):
    dm.upload("ds2", "ds2.txt", base64.b64encode(b"stable content").decode())
    result = dm.validate("ds2")
    assert result["valid"] is True


def test_versioning_increments_on_reupload(dm):
    dm.upload("v", "v.txt", base64.b64encode(b"v1").decode())
    dm.upload("v", "v.txt", base64.b64encode(b"v2").decode())
    entry = dm._get_entry("v")
    assert len(entry["versions"]) == 2
    latest = dm.inspect("v")
    assert latest["version"] == 2


def test_inspect_unknown_dataset_raises(dm):
    with pytest.raises(DatasetError):
        dm.inspect("nope")


def test_convert_csv_to_json(dm):
    csv_content = b"name,age\nAlice,30\nBob,25\n"
    dm.upload("people", "people.csv", base64.b64encode(csv_content).decode())
    result = dm.convert_csv_to_json("people", "people.json")
    assert result["row_count"] == 2
    output = json.loads(dm.path_guard.resolve("people.json").read_text())
    assert output[0]["name"] == "Alice"


def test_cache_from_url_rejects_disallowed_scheme(dm):
    with pytest.raises(DatasetError):
        dm.cache_from_url("bad", "ftp://example.com/file.txt", "file.txt")


def test_cache_from_url_success(dm):
    fake_response = MagicMock()
    fake_response.read.side_effect = [b"hello world", b""]
    fake_response.__enter__ = lambda self: fake_response
    fake_response.__exit__ = lambda self, *a: None

    with patch("urllib.request.urlopen", return_value=fake_response):
        entry = dm.cache_from_url("web_ds", "https://example.com/data.txt", "web.txt")

    assert entry["size_bytes"] == len(b"hello world")


def test_unimplemented_source_connectors_raise_clear_error(dm):
    for name, connector in SOURCE_CONNECTORS.items():
        with pytest.raises(DatasetError) as excinfo:
            connector.fetch("some-id", dm, "name", "path")
        assert name in str(excinfo.value.suggestion) or "docs/DATASETS.md" in excinfo.value.suggestion
