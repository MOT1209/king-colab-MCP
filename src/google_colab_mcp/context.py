"""Wires together config, security, and the Colab/job managers.

One `ServerContext` instance is built at startup and passed to every tool
handler — nothing here is agent- or framework-specific.
"""
from __future__ import annotations

from dataclasses import dataclass

from .colab.artifact_manager import ArtifactManager
from .colab.execution_manager import ExecutionManager
from .colab.notebook_manager import NotebookManager
from .colab.remote_fs import RemoteFileManager
from .colab.runtime_manager import RuntimeManager
from .colab.session_manager import SessionManager
from .config import Settings, get_settings
from .jobs.job_manager import JobManager
from .logging.audit import AuditLogger
from .security.path_guard import PathGuard
from .security.rate_limit import RateLimiter


@dataclass
class ServerContext:
    settings: Settings
    path_guard: PathGuard
    artifact_guard: PathGuard
    session_manager: SessionManager
    execution_manager: ExecutionManager
    runtime_manager: RuntimeManager
    notebook_manager: NotebookManager
    remote_file_manager: RemoteFileManager
    artifact_manager: ArtifactManager
    job_manager: JobManager
    rate_limiter: RateLimiter
    audit_logger: AuditLogger

    @classmethod
    def build(cls, settings: Settings | None = None) -> "ServerContext":
        settings = settings or get_settings()
        path_guard = PathGuard(settings.workspace_root)
        artifact_guard = PathGuard(settings.artifact_root)
        session_manager = SessionManager()
        execution_manager = ExecutionManager(session_manager)
        return cls(
            settings=settings,
            path_guard=path_guard,
            artifact_guard=artifact_guard,
            session_manager=session_manager,
            execution_manager=execution_manager,
            runtime_manager=RuntimeManager(execution_manager),
            notebook_manager=NotebookManager(path_guard, execution_manager),
            remote_file_manager=RemoteFileManager(execution_manager, settings.remote_workspace_root),
            artifact_manager=ArtifactManager(artifact_guard),
            job_manager=JobManager(max_concurrent_jobs=settings.max_concurrent_jobs),
            rate_limiter=RateLimiter(settings.max_requests_per_minute),
            audit_logger=AuditLogger(settings.audit_log_path),
        )

    def shutdown(self) -> None:
        self.session_manager.close_all()
