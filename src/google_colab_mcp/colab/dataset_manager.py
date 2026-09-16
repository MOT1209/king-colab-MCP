"""Dataset lifecycle management: upload/download/validate/inspect/cache/
version/convert for datasets living under the local sandboxed workspace
(the server host's filesystem, via `PathGuard` — distinct from
`remote_fs.py`, which manages files *inside* a connected runtime).

Scope note (see docs/DATASETS.md): local files and `http(s)://` URLs are
fully implemented. Hugging Face / Kaggle / Google Drive / GitHub connectors
are documented extension points (`SOURCE_CONNECTORS`) that raise a clear
`DatasetError` rather than silently no-op-ing — wiring a real connector in
is a `DatasetSource` subclass, not a rewrite of this manager.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import time
import urllib.request
from pathlib import Path
from typing import Any

from ..security.path_guard import PathGuard
from ..utils.errors import DatasetError, ResourceExhaustedError

_ALLOWED_URL_SCHEMES = ("http", "https")


def _sha256_of_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


class DatasetManager:
    def __init__(self, path_guard: PathGuard, max_download_bytes: int = 500_000_000):
        self.path_guard = path_guard
        self.max_download_bytes = max_download_bytes
        self._index_path = self.path_guard.root / "_dataset_index.json"
        if not self._index_path.exists():
            self._index_path.write_text("{}")

    def _read_index(self) -> dict[str, Any]:
        return json.loads(self._index_path.read_text())

    def _write_index(self, index: dict[str, Any]) -> None:
        self._index_path.write_text(json.dumps(index, indent=2))

    def _register(self, name: str, relative_path: str, source: str) -> dict[str, Any]:
        resolved = self.path_guard.resolve(relative_path)
        checksum = _sha256_of_file(resolved)
        size_bytes = resolved.stat().st_size
        index = self._read_index()
        entry = index.setdefault(name, {"name": name, "versions": []})
        version_number = len(entry["versions"]) + 1
        version = {
            "version": version_number,
            "path": relative_path,
            "checksum_sha256": checksum,
            "size_bytes": size_bytes,
            "source": source,
            "registered_at": time.time(),
        }
        entry["versions"].append(version)
        self._write_index(index)
        return {"name": name, **version}

    def upload(self, name: str, path: str, content_base64: str) -> dict[str, Any]:
        import base64

        resolved = self.path_guard.resolve(path)
        data = base64.b64decode(content_base64)
        if len(data) > self.max_download_bytes:
            raise ResourceExhaustedError(
                f"Upload of {len(data)} bytes exceeds the {self.max_download_bytes}-byte limit.",
            )
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_bytes(data)
        return self._register(name, path, source="upload")

    def cache_from_url(self, name: str, url: str, path: str) -> dict[str, Any]:
        scheme = url.split("://", 1)[0].lower() if "://" in url else ""
        if scheme not in _ALLOWED_URL_SCHEMES:
            raise DatasetError(
                f"Unsupported URL scheme: {scheme!r}",
                suggestion=f"Only {_ALLOWED_URL_SCHEMES} URLs are fetched directly by the server.",
            )
        resolved = self.path_guard.resolve(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)

        request = urllib.request.Request(url, headers={"User-Agent": "google-colab-mcp/dataset-manager"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - scheme is checked above
                written = 0
                with open(resolved, "wb") as f:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        written += len(chunk)
                        if written > self.max_download_bytes:
                            raise ResourceExhaustedError(
                                f"Download exceeded the {self.max_download_bytes}-byte limit; aborted.",
                            )
                        f.write(chunk)
        except ResourceExhaustedError:
            resolved.unlink(missing_ok=True)
            raise
        except Exception as exc:  # noqa: BLE001
            resolved.unlink(missing_ok=True)
            raise DatasetError(f"Failed to download dataset from {url}", details=str(exc)) from exc

        return self._register(name, path, source=url)

    def download(self, name: str, version: int | None = None) -> dict[str, Any]:
        import base64

        entry = self._get_entry(name)
        ver = self._get_version(entry, version)
        resolved = self.path_guard.resolve(ver["path"])
        if not resolved.exists():
            raise DatasetError(f"Dataset file missing on disk: {ver['path']}")
        data = resolved.read_bytes()
        return {"name": name, "version": ver["version"], "content_base64": base64.b64encode(data).decode()}

    def validate(self, name: str, version: int | None = None) -> dict[str, Any]:
        entry = self._get_entry(name)
        ver = self._get_version(entry, version)
        resolved = self.path_guard.resolve(ver["path"])
        if not resolved.exists():
            return {"name": name, "version": ver["version"], "valid": False, "reason": "file missing"}
        current_checksum = _sha256_of_file(resolved)
        valid = current_checksum == ver["checksum_sha256"]
        return {
            "name": name,
            "version": ver["version"],
            "valid": valid,
            "expected_checksum": ver["checksum_sha256"],
            "actual_checksum": current_checksum,
        }

    def inspect(self, name: str, version: int | None = None, preview_bytes: int = 2000) -> dict[str, Any]:
        entry = self._get_entry(name)
        ver = self._get_version(entry, version)
        resolved = self.path_guard.resolve(ver["path"])
        preview = None
        try:
            with open(resolved, "rb") as f:
                raw = f.read(preview_bytes)
            preview = raw.decode("utf-8", errors="replace")
        except OSError:
            pass
        return {
            "name": name,
            "version": ver["version"],
            "size_bytes": ver["size_bytes"],
            "checksum_sha256": ver["checksum_sha256"],
            "source": ver["source"],
            "preview": preview,
        }

    def list_datasets(self) -> list[dict[str, Any]]:
        return list(self._read_index().values())

    def convert_csv_to_json(self, name: str, output_path: str, version: int | None = None) -> dict[str, Any]:
        entry = self._get_entry(name)
        ver = self._get_version(entry, version)
        source_path = self.path_guard.resolve(ver["path"])
        target_path = self.path_guard.resolve(output_path)
        with open(source_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(rows, indent=2))
        return {"name": name, "output_path": output_path, "row_count": len(rows)}

    def _get_entry(self, name: str) -> dict[str, Any]:
        index = self._read_index()
        if name not in index:
            raise DatasetError(f"No such dataset: {name}", suggestion="Use colab_list_datasets to see registered datasets.")
        return index[name]

    def _get_version(self, entry: dict[str, Any], version: int | None) -> dict[str, Any]:
        versions = entry["versions"]
        if not versions:
            raise DatasetError(f"Dataset {entry['name']!r} has no versions registered.")
        if version is None:
            return versions[-1]
        for v in versions:
            if v["version"] == version:
                return v
        raise DatasetError(f"No such version {version} for dataset {entry['name']!r}.")


class DatasetSource:
    """Extension point for a hosted dataset connector (Hugging Face, Kaggle,
    Google Drive, GitHub, ...). Not implemented in this release — see
    docs/DATASETS.md for the interface a real connector should provide."""

    name: str = "base"

    def fetch(self, identifier: str, dest: DatasetManager, dataset_name: str, path: str) -> dict[str, Any]:
        raise DatasetError(
            f"The '{self.name}' dataset source is not implemented in this release.",
            suggestion=(
                "Use colab_cache_dataset_from_url for a direct http(s) download, or "
                "colab_upload_dataset for local content, in the meantime. "
                "See docs/DATASETS.md for the DatasetSource interface to add real support."
            ),
        )


SOURCE_CONNECTORS: dict[str, DatasetSource] = {
    "huggingface": DatasetSource(),
    "kaggle": DatasetSource(),
    "google_drive": DatasetSource(),
    "github": DatasetSource(),
}
for _name, _source in SOURCE_CONNECTORS.items():
    _source.name = _name
