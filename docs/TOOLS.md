# Tool Reference

All tools return either `{"success": true, "result": {...}}` or
`{"success": false, "error": {"type", "message", "details", "suggestion"}}`.
Full JSON Schemas are also available live via the MCP `tools/list` method —
this document is a human-readable summary.

## Runtime & sessions (`runtime_tools`)

| Tool | Description |
|---|---|
| `colab_create_session` | Open a new runtime session (attach to a kernel connection file, or launch a local kernel). |
| `colab_get_runtime` | Active sessions, Python version, CUDA/torch availability. |
| `colab_get_gpu` | GPU device name(s), VRAM, count. |
| `colab_get_cpu` | Logical/physical core count, utilization. |
| `colab_get_memory` | RAM total/available/used. |
| `colab_get_disk` | Disk total/used/free. |
| `colab_restart_runtime` | Restart a session's kernel (clears all state). |

## Execution (`execution_tools`)

| Tool | Description |
|---|---|
| `colab_execute_code` | Run Python code synchronously; returns stdout/stderr/result/display data. |
| `colab_stop_execution` | Interrupt whatever is currently executing in a session. |

## Notebooks (`notebook_tools`)

| Tool | Description |
|---|---|
| `colab_create_notebook` | Create an empty `.ipynb`. |
| `colab_get_notebook` | Read cells + metadata. |
| `colab_update_notebook` | Replace the entire cell list. |
| `colab_add_cell` / `colab_edit_cell` / `colab_delete_cell` | Single-cell CRUD. |
| `colab_execute_cell` | Execute one cell by index. |
| `colab_execute_notebook` | Execute every code cell in order. |
| `colab_export_notebook` | Export as raw `.ipynb` JSON or a flattened Python script. |

## Files inside the runtime (`file_tools`)

All paths are relative to `COLAB_REMOTE_WORKSPACE_ROOT` (default
`/content/mcp_workspace`) and cannot escape it.

| Tool | Description |
|---|---|
| `colab_upload_file` / `colab_download_file` | Base64 binary transfer. |
| `colab_read_file` / `colab_write_file` | Text file I/O. |
| `colab_list_files` | List a directory. |
| `colab_delete_file` | Delete a file or directory (recursive). |
| `colab_move_file` | Move/rename. |
| `colab_create_directory` | `mkdir -p` equivalent. |

## Packages (`package_tools`)

| Tool | Description |
|---|---|
| `colab_install_package` | `pip install` a package/spec (e.g. `torch==2.3.0`). |
| `colab_uninstall_package` | `pip uninstall`. |
| `colab_list_packages` | `pip list --format json`. |
| `colab_get_package_version` | `pip show` a specific package. |

## Training / ML (`training_tools`)

No framework is imposed — whatever the submitted code imports (PyTorch,
TensorFlow, Transformers, scikit-learn, XGBoost, ...) resolves inside the
runtime.

| Tool | Description |
|---|---|
| `colab_run_training` | Start a training script as a background job; returns `job_id` immediately. |
| `colab_stop_training` | Interrupt a running training job. |
| `colab_evaluate_model` | Run evaluation code synchronously. |
| `colab_save_model` | Run save code, optionally register the artifact. |
| `colab_export_model` | Run export code (ONNX/TorchScript/etc.), optionally register the artifact. |

## Jobs & artifacts (`job_tools`)

| Tool | Description |
|---|---|
| `colab_get_job` | Status/progress/result for a `job_id`. |
| `colab_cancel_job` | Request cancellation. |
| `colab_get_logs` | Job log lines (optionally last N). |
| `colab_list_jobs` | All jobs, optionally filtered by status. |
| `colab_get_artifacts` | Artifacts for one job, or all jobs. |

Job states: `queued` → `starting` → `running` → one of
`completed` / `failed` / `cancelled` / `timeout`.

## Resources

| URI | Contents |
|---|---|
| `colab://runtime` | Active sessions + connection state. |
| `colab://jobs` | All known jobs. |
| `colab://notebooks` | Notebooks found under the workspace root. |
| `colab://artifacts` | All registered artifacts, grouped by job. |

## Prompts

| Name | Purpose |
|---|---|
| `run_with_gpu_if_available` | Walks an agent through checking for a GPU before running code. |
| `train_and_monitor` | Walks an agent through starting a training job and polling it to completion. |
