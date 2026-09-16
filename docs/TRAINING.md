# ML Training

This server imposes **no ML framework**. `colab_run_training` submits
whatever Python training script you give it to a runtime session as a
background job — PyTorch, TensorFlow, Transformers, scikit-learn, XGBoost,
or anything else the runtime has installed resolves inside that runtime,
not here.

## Tools

| Tool | What it does |
|---|---|
| `colab_run_training` | Submit a training script as a background job; returns `job_id` immediately (never blocks the MCP call). |
| `colab_get_job` / `colab_get_logs` | Poll status, progress, structured `metrics`, and log lines. |
| `colab_pause_job` / `colab_resume_job` | Cooperative pause/resume — see below. |
| `colab_stop_training` | Interrupt the session's kernel and mark the job cancelled. |
| `colab_evaluate_model` | Run evaluation code synchronously (not job-based — expected to be fast). |
| `colab_save_model` / `colab_export_model` | Run save/export code, optionally registering the resulting file as a job artifact. |

## The job/session/runtime link

Every job created by `colab_run_training` records `session_id` and
`runtime_id` (the session and underlying runtime it ran against) on the
`Job` object itself — `colab_get_job` surfaces both, so you can trace a
training run back to exactly which provider/kernel it used, and
`colab_get_artifacts(job_id)` lists what it produced.

## Metrics vs. logs

Free-text `colab_get_logs` output is for humans skimming progress.
Structured metrics (loss curves, accuracy, etc.) belong in `job.metrics`
instead — have your training code print them in a way you parse and feed
into `Job.record_metric()` if you're extending this server, or, for now,
keep numeric results in the job's returned `result` dict from
`colab_run_training`'s underlying code.

## Pause/resume: what "cooperative" means

`colab_pause_job` sets a flag (`job.pause_requested`) and, if the job is
`running`, marks it `paused`. **This does not stop a training loop by
itself.** A long-running script has no way to be paused mid-`for` loop by
an external signal without either:

- polling a shared flag from inside the loop (not possible today, since
  the job's code runs *inside the connected kernel*, not in this
  server's process — there's no shared-memory flag to poll), or
- being interrupted via `colab_stop_execution`/`colab_stop_training` and
  restarted from a checkpoint.

So today, `colab_pause_job`/`colab_resume_job` update job bookkeeping
(useful for a job orchestrator to see "the user asked to pause this") but
do **not** actually halt in-kernel execution — that is stated here
explicitly rather than implied by the tool's name. Real pause support
would need the training script itself to check in with the server
periodically (e.g. via a small polling loop calling back into
`colab_get_job` for its own `pause_requested` flag) — which is possible to
build today (any code you submit *can* poll `colab_get_job` on itself if
you write it that way) but isn't automatic.

## Checkpoints / resume-from-checkpoint

Not implemented as a dedicated tool. Use `colab_save_model` /
`colab_write_file` to persist a checkpoint inside your training code at
whatever cadence you choose, and have a subsequent `colab_run_training`
call load it at startup — this server doesn't need to know the checkpoint
format (Torch `.pt`, TF `SavedModel`, a HF `Trainer` checkpoint dir, ...)
to support this pattern.
