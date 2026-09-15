"""ID generation helpers shared across the codebase."""
import uuid


def new_id(prefix: str) -> str:
    """Generate a short, prefixed, collision-resistant identifier (e.g. 'job_ab12cd34')."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
