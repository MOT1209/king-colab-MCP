from .base import ProviderDiscoveryResult, RuntimeProvider, RuntimeState
from .colab_provider import ColabProvider
from .docker_provider import DockerProvider
from .local_jupyter_provider import LocalJupyterProvider
from .remote_jupyter_provider import RemoteJupyterProvider

PROVIDER_REGISTRY: dict[str, type[RuntimeProvider]] = {
    ColabProvider.provider_id: ColabProvider,
    LocalJupyterProvider.provider_id: LocalJupyterProvider,
    RemoteJupyterProvider.provider_id: RemoteJupyterProvider,
    DockerProvider.provider_id: DockerProvider,
}

__all__ = [
    "ProviderDiscoveryResult",
    "RuntimeProvider",
    "RuntimeState",
    "ColabProvider",
    "LocalJupyterProvider",
    "RemoteJupyterProvider",
    "DockerProvider",
    "PROVIDER_REGISTRY",
]
