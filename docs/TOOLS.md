# Tool Reference

All tools return either `{"success": true, "result": {...}}` or
`{"success": false, "error": {"type", "message", "details", "suggestion",
"retryable"}}`. Full JSON Schemas are also available live via the MCP
`tools/list` method — this document is a human-readable summary of all 59
tools.

## Runtime & sessions (`runtime_tools`)

| Tool | Description |
|---|---|
| `colab_create_session` | Open a session against a `RuntimeProvider`: `colab` (verified real Colab — see [COLAB.md](COLAB.md)), `local_jupyter` (default), `remote_jupyter`, or `docker`. Accepts `provider_config`, `label`, `owner`, `permissions`. |
| `colab_get_session` | One session's status/provider/owner/permissions. |
| `colab_list_sessions` | All sessions and their status. |
| `colab_reconnect_session` | Force a reconnect using the session's original provider/config. |
| `colab_close_session` | Disconnect and remove a session (tears down the container for `docker`). |
| `colab_session_health` | On-demand health check (what the background `HealthMonitor` also runs periodically). |
| `colab_get_runtime` | Active sessions, Python version, CUDA/torch availability. |
| `colab_get_gpu` | GPU device name(s)/VRAM/count, via nvidia-smi, pynvml, torch, *and* TensorFlow (whichever is available). |
| `colab_get_cpu` | Logical/physical core count, utilization. |
| `colab_get_memory` | RAM total/available/used. |
| `colab_get_disk` | Disk total/used/free. |
| `colab_restart_runtime` | Restart a session's kernel (clears all state). *Dangerous.* |

## Execution (`execution_tools`)

| Tool | Description |
|---|---|
| `colab_execute_code` | Run Python code synchronously; returns stdout/stderr/result/display data, truncated at `MAX_OUTPUT_BYTES` with `output_truncated: true` if exceeded. *Dangerous.* |
| `colab_stop_execution` | Interrupt whatever is currently executing in a session. |

## Notebooks (`notebook_tools`)

| Tool | Description |
|---|---|
| `colab_create_notebook` | Create an empty `.ipynb`. |
| `colab_get_notebook` | Read cells + metadata. |
| `colab_update_notebook` | Replace the entire cell list. |
| `colab_add_cell` / `colab_edit_cell` / `colab_delete_cell` | Single-cell CRUD. `colab_delete_cell` is *dangerous*. |
| `colab_execute_cell` / `colab_execute_notebook` | Execute one cell, or every code cell in order. Both *dangerous*. |
| `colab_export_notebook` | Export as raw `.ipynb` JSON or a flattened Python script. |

## Files inside the runtime (`file_tools`)

All paths are relative to `COLAB_REMOTE_WORKSPACE_ROOT` (default
`/content/mcp_workspace`), cannot escape it, and uploads are capped at
`MAX_FILE_SIZE_BYTES`.

| Tool | Description |
|---|---|
| `colab_upload_file` / `colab_download_file` | Base64 binary transfer. |
| `colab_read_file` / `colab_write_file` | Text file I/O. |
| `colab_list_files` | List a directory. |
| `colab_delete_file` | Delete a file or directory (recursive). *Dangerous.* |
| `colab_move_file` | Move/rename. *Dangerous.* |
| `colab_create_directory` | `mkdir -p` equivalent. |

## Packages & environments (`package_tools`, backed by `EnvironmentManager`)

| Tool | Description |
|---|---|
| `colab_install_package` | `pip install` a package/spec (e.g. `torch==2.3.0`). *Dangerous.* |
| `colab_uninstall_package` | `pip uninstall`. *Dangerous.* |
| `colab_list_packages` | `pip list --format json`. |
| `colab_get_package_version` | `pip show` a specific package. |
| `colab_export_requirements` | `pip freeze` as a string. |
| `colab_install_requirements` | Install every line of a requirements.txt-formatted string. *Dangerous.* |
| `colab_save_environment_profile` | Snapshot installed packages as a named `EnvironmentProfile`. |
| `colab_apply_environment_profile` | Reinstall everything from a saved profile. |
| `colab_list_environment_profiles` | List saved profile names. |

## Datasets (`dataset_tools`, backed by `DatasetManager`)

Local upload + `http(s)://` caching only — see [DATASETS.md](DATASETS.md)
for scope, the SSRF note on `colab_cache_dataset_from_url`, and why
Hugging Face/Kaggle/Google Drive/GitHub connectors raise a clear "not
implemented" error instead of pretending to work.

| Tool | Description |
|---|---|
| `colab_upload_dataset` | Register base64 content as a new checksummed, versioned dataset. |
| `colab_cache_dataset_from_url` | Download an http(s) URL into the dataset store and register it. *Dangerous.* |
| `colab_download_dataset` | Get a dataset (or a specific version) as base64. |
| `colab_validate_dataset` | Recompute and compare checksums. |
| `colab_inspect_dataset` | Metadata + a text preview of the first bytes. |
| `colab_list_datasets` | List all registered datasets and their versions. |
| `colab_convert_dataset_csv_to_json` | The one implemented format conversion. |

## Training / ML (`training_tools`)

No framework is imposed — whatever the submitted code imports (PyTorch,
TensorFlow, Transformers, scikit-learn, XGBoost, ...) resolves inside the
runtime. See [TRAINING.md](TRAINING.md) for the job/session/runtime link
and what pause/resume actually does.

| Tool | Description |
|---|---|
| `colab_run_training` | Start a training script as a background job; returns `job_id` immediately. *Dangerous.* |
| `colab_stop_training` | Interrupt a running training job. |
| `colab_evaluate_model` | Run evaluation code synchronously. |
| `colab_save_model` | Run save code, optionally register the artifact. *Dangerous.* |
| `colab_export_model` | Run export code (ONNX/TorchScript/etc.), optionally register the artifact. *Dangerous.* |

## Jobs & artifacts (`job_tools`)

| Tool | Description |
|---|---|
| `colab_get_job` | Status/progress/`metrics`/result for a `job_id`, including which `session_id`/`runtime_id` it ran on. |
| `colab_cancel_job` | Request cancellation. |
| `colab_pause_job` / `colab_resume_job` | Cooperative pause/resume — bookkeeping only; see [TRAINING.md](TRAINING.md). |
| `colab_get_logs` | Job log lines (optionally last N). |
| `colab_list_jobs` | All jobs, optionally filtered by status. |
| `colab_get_artifacts` | Artifacts for one job, or all jobs. |

Job states: `queued` → `starting` → `running` ⇄ `paused` → one of
`completed` / `failed` / `cancelled` / `timeout`.

*Dangerous* means the tool is on `security/dangerous_tools.py`'s list —
with `DANGEROUS_TOOLS_REQUIRE_CONFIRM=true`, it must be called with
`"confirm": true`.

## Resources

| URI | Contents |
|---|---|
| `colab://runtime` | Active sessions + connection state. |
| `colab://sessions` | Full detail (provider, status, owner, permissions) for every session. |
| `colab://jobs` | All known jobs. |
| `colab://notebooks` | Notebooks found under the workspace root. |
| `colab://artifacts` | All registered artifacts, grouped by job. |
| `colab://environments` | Saved `EnvironmentProfile` names. |
| `colab://datasets` | All registered datasets and their versions. |

## Prompts

| Name | Purpose |
|---|---|
| `run_with_gpu_if_available` | Walks an agent through checking for a GPU before running code. |
| `train_and_monitor` | Walks an agent through starting a training job and polling it to completion. |
