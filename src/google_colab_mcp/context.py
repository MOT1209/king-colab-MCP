"""Wires together config, security, and the Colab/job managers.

One `ServerContext` instance is built at startup and passed to every tool
handler — nothing here is agent- or framework-specific.
"""
from __future__ import annotations

from dataclasses import dataclass

from .colab.artifact_manager import ArtifactManager
from .colab.dataset_manager import DatasetManager
from .colab.environment_manager import EnvironmentManager
from .colab.execution_manager import ExecutionManager
from .colab.health_monitor import HealthMonitor
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
    environment_guard: PathGuard
    dataset_guard: PathGuard
    session_manager: SessionManager
    execution_manager: ExecutionManager
    runtime_manager: RuntimeManager
    notebook_manager: NotebookManager
    remote_file_manager: RemoteFileManager
    artifact_manager: ArtifactManager
    environment_manager: EnvironmentManager
    dataset_manager: DatasetManager
    job_manager: JobManager
    rate_limiter: RateLimiter
    audit_logger: AuditLogger
    health_monitor: HealthMonitor

    @classmethod
    def build(cls, settings: Settings | None = None) -> "ServerContext":
        settings = settings or get_settings()
        path_guard = PathGuard(settings.workspace_root)
        artifact_guard = PathGuard(settings.artifact_root)
        environment_guard = PathGuard(settings.environment_root)
        dataset_guard = PathGuard(settings.dataset_root)
        session_manager = SessionManager()
        execution_manager = ExecutionManager(session_manager, max_output_bytes=settings.max_output_bytes)
        health_monitor = HealthMonitor(
            session_manager,
            interval_seconds=settings.health_check_interval_seconds,
            max_reconnect_attempts=settings.max_reconnect_attempts,
        )
        if settings.health_monitor_enabled:
            health_monitor.start()
        return cls(
            settings=settings,
            path_guard=path_guard,
            artifact_guard=artifact_guard,
            environment_guard=environment_guard,
            dataset_guard=dataset_guard,
            session_manager=session_manager,
            execution_manager=execution_manager,
            runtime_manager=RuntimeManager(execution_manager),
            notebook_manager=NotebookManager(path_guard, execution_manager),
            remote_file_manager=RemoteFileManager(
                execution_manager, settings.remote_workspace_root, max_file_size_bytes=settings.max_file_size_bytes
            ),
            artifact_manager=ArtifactManager(artifact_guard),
            environment_manager=EnvironmentManager(execution_manager, environment_guard),
            dataset_manager=DatasetManager(dataset_guard, max_download_bytes=settings.max_file_size_bytes),
            job_manager=JobManager(max_concurrent_jobs=settings.max_concurrent_jobs),
            rate_limiter=RateLimiter(settings.max_requests_per_minute),
            audit_logger=AuditLogger(settings.audit_log_path),
            health_monitor=health_monitor,
        )

    def shutdown(self) -> None:
        self.health_monitor.stop()
        self.session_manager.close_all()
