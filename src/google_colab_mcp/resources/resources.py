"""MCP Resources exposing server state as readable URIs.

    colab://runtime       — summary: active sessions + hardware/software info
    colab://sessions      — full detail on every runtime session
    colab://jobs          — all known jobs and their status
    colab://notebooks     — notebooks under the workspace root
    colab://artifacts     — all registered artifacts, grouped by job
    colab://environments  — saved EnvironmentProfile names
    colab://datasets      — all registered datasets and their versions
"""
from __future__ import annotations

import json
from typing import Any

from ..context import ServerContext

RESOURCE_DEFS = [
    {"uri": "colab://runtime", "name": "Runtime status", "mime_type": "application/json",
     "description": "Active runtime sessions and hardware/software info."},
    {"uri": "colab://sessions", "name": "Sessions", "mime_type": "application/json",
     "description": "Full detail (provider, status, owner, permissions) for every runtime session."},
    {"uri": "colab://jobs", "name": "Jobs", "mime_type": "application/json",
     "description": "All known jobs (training runs, batch executions) and their status."},
    {"uri": "colab://notebooks", "name": "Notebooks", "mime_type": "application/json",
     "description": "Notebooks (.ipynb) found under the sandboxed workspace root."},
    {"uri": "colab://artifacts", "name": "Artifacts", "mime_type": "application/json",
     "description": "All registered artifacts (models, datasets, logs, reports), grouped by job."},
    {"uri": "colab://environments", "name": "Environment profiles", "mime_type": "application/json",
     "description": "Saved EnvironmentProfile names, restorable via colab_apply_environment_profile."},
    {"uri": "colab://datasets", "name": "Datasets", "mime_type": "application/json",
     "description": "All registered datasets and their versions."},
]


def list_resources() -> list[dict[str, Any]]:
    return RESOURCE_DEFS


def read_resource(ctx: ServerContext, uri: str) -> str:
    if uri == "colab://runtime":
        sessions = ctx.session_manager.list_sessions()
        payload = {"sessions": [s.to_dict() for s in sessions]}
    elif uri == "colab://sessions":
        payload = {"sessions": [s.to_dict() for s in ctx.session_manager.list_sessions()]}
    elif uri == "colab://jobs":
        payload = {"jobs": [j.to_dict() for j in ctx.job_manager.list_jobs()]}
    elif uri == "colab://notebooks":
        notebooks = [
            str(p.relative_to(ctx.path_guard.root))
            for p in ctx.path_guard.root.rglob("*.ipynb")
        ]
        payload = {"notebooks": notebooks}
    elif uri == "colab://artifacts":
        payload = {"artifacts_by_job": ctx.artifact_manager.list_all()}
    elif uri == "colab://environments":
        payload = {"profiles": ctx.environment_manager.list_profiles()}
    elif uri == "colab://datasets":
        payload = {"datasets": ctx.dataset_manager.list_datasets()}
    else:
        raise KeyError(f"Unknown resource URI: {uri}")

    return json.dumps(payload, indent=2, default=str)
