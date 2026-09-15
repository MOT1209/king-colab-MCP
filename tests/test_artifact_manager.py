from google_colab_mcp.colab.artifact_manager import ArtifactManager
from google_colab_mcp.security.path_guard import PathGuard


def test_register_and_list_for_job(tmp_path):
    guard = PathGuard(tmp_path)
    (tmp_path / "model.bin").write_bytes(b"weights")
    manager = ArtifactManager(guard)

    entry = manager.register("job_1", "model", "model", "model.bin")
    assert entry["size_bytes"] == len(b"weights")

    listed = manager.list_for_job("job_1")
    assert len(listed) == 1
    assert listed[0]["name"] == "model"


def test_list_all_groups_by_job(tmp_path):
    guard = PathGuard(tmp_path)
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    manager = ArtifactManager(guard)
    manager.register("job_1", "a", "log", "a.txt")
    manager.register("job_2", "b", "log", "b.txt")

    all_artifacts = manager.list_all()
    assert set(all_artifacts.keys()) == {"job_1", "job_2"}


def test_list_for_unknown_job_returns_empty(tmp_path):
    guard = PathGuard(tmp_path)
    manager = ArtifactManager(guard)
    assert manager.list_for_job("nope") == []
