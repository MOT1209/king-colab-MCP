"""MCP Prompts: reusable instruction templates any MCP client can surface to its model."""
from __future__ import annotations

from typing import Any

PROMPT_DEFS = [
    {
        "name": "run_with_gpu_if_available",
        "description": "Guides an agent through checking for a GPU and running code, using GPU-aware code if present.",
        "arguments": [{"name": "code", "description": "The Python code to run.", "required": True}],
    },
    {
        "name": "train_and_monitor",
        "description": "Guides an agent through starting a training job and polling it to completion.",
        "arguments": [{"name": "training_code", "description": "The training script to run.", "required": True}],
    },
]


def get_prompt(name: str, arguments: dict[str, Any]) -> list[dict[str, Any]]:
    if name == "run_with_gpu_if_available":
        code = arguments.get("code", "")
        text = (
            "1. Call colab_get_runtime to see active sessions.\n"
            "2. Call colab_get_gpu to check whether a GPU is available.\n"
            "3. Call colab_execute_code with the following code (adapt it to use "
            "`cuda` if colab_get_gpu reported an available device, else `cpu`):\n\n"
            f"```python\n{code}\n```\n\n"
            "4. Report stdout/stderr and the result back to the user."
        )
        return [{"role": "user", "content": {"type": "text", "text": text}}]

    if name == "train_and_monitor":
        training_code = arguments.get("training_code", "")
        text = (
            "1. Call colab_run_training with this training code to get a job_id:\n\n"
            f"```python\n{training_code}\n```\n\n"
            "2. Poll colab_get_job with that job_id until status is 'completed', 'failed', "
            "'cancelled', or 'timeout'.\n"
            "3. Call colab_get_logs to show recent progress while it runs.\n"
            "4. Once completed, call colab_get_artifacts with the job_id to list produced artifacts."
        )
        return [{"role": "user", "content": {"type": "text", "text": text}}]

    raise KeyError(f"Unknown prompt: {name}")
