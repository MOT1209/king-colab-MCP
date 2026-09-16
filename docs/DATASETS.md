# Datasets

`colab/dataset_manager.py::DatasetManager` manages datasets **on this
server's local sandboxed filesystem** (via `PathGuard`, under
`COLAB_DATASET_ROOT`) — distinct from `remote_fs.py`, which manages files
*inside a connected runtime*. Every registered dataset gets a SHA-256
checksum and an incrementing version number.

## What's implemented

| Tool | What it does |
|---|---|
| `colab_upload_dataset` | Register base64-encoded content as a new dataset version. |
| `colab_cache_dataset_from_url` | Download an `http(s)://` URL directly into the dataset store and register it. |
| `colab_download_dataset` | Get a dataset (or a specific version) back as base64. |
| `colab_validate_dataset` | Recompute the checksum and compare against what was recorded — detects tampering/corruption. |
| `colab_inspect_dataset` | Metadata (size, checksum, source) + a text preview of the first bytes. |
| `colab_list_datasets` | List all registered datasets and their versions. |
| `colab_convert_dataset_csv_to_json` | The one implemented format conversion. |

## Security note on `colab_cache_dataset_from_url`

This tool makes the **MCP server's own host** fetch a URL — not the
connected runtime. That's a real SSRF surface: a malicious or careless
caller could point it at an internal service (`http://169.254.169.254/...`,
an internal admin panel, etc.) and read the response back as "dataset
content". Mitigations actually in place:

- Only `http://`/`https://` schemes are accepted (no `file://`, `ftp://`,
  etc.).
- Downloads are size-capped (`MAX_FILE_SIZE_BYTES`) and aborted mid-stream
  if exceeded.

**Not implemented**: DNS-rebinding protection, an IP allow/deny list, or
blocking link-local/private address ranges. If you expose this server to
untrusted callers, either disable this tool (`DENIED_TOOLS`) or put a
network-level egress filter in front of the host running it — this is a
genuine gap, not a solved problem.

## What's *not* implemented: hosted dataset connectors

`SOURCE_CONNECTORS` in `dataset_manager.py` defines the extension point
for Hugging Face, Kaggle, Google Drive, and GitHub — each currently a
`DatasetSource` instance whose `.fetch()` raises `DatasetError` with a
clear "not implemented, here's what to use instead" message. This is
intentional: claiming these worked without building the actual
credential/pagination/API-specific logic each one needs would be
dishonest. To add a real one:

```python
class HuggingFaceDatasetSource(DatasetSource):
    name = "huggingface"

    def fetch(self, identifier: str, dest: DatasetManager, dataset_name: str, path: str) -> dict:
        # e.g. use `huggingface_hub.hf_hub_download`, verify the returned
        # file, then dest.upload(...) or write directly under dest.path_guard.root
        # and call dest._register(...).
        ...
```

Then swap the registry entry in `SOURCE_CONNECTORS["huggingface"]`. Doing
this well means handling that connector's own auth (an HF token, a Kaggle
API key, a Google Drive OAuth flow, a GitHub token for private repos) —
none of which this server manages today (see
[AUTHENTICATION.md](AUTHENTICATION.md) for the same caveat applied to
MCP-level auth).

## Format conversion scope

Only CSV → JSON is implemented, using the standard library (`csv`,
`json`) — no `pandas`/`pyarrow` dependency added to the server itself.
Parquet, Arrow, or other tabular conversions are not implemented; if you
need them, run the conversion as ordinary Python via `colab_execute_code`
inside a runtime that has the relevant library installed, which needs no
changes to this server at all.
