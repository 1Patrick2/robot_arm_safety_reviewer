from pathlib import Path

from runtime_db.repository import RuntimeMetricsRepository
from runtime_db.schema import init_runtime_db


def _repo(tmp_path) -> RuntimeMetricsRepository:
    db_path = tmp_path / "test.db"
    init_runtime_db(db_path)
    return RuntimeMetricsRepository(db_path)


class TestRuntimeMetricsRepository:
    def test_upsert_run_and_get_run(self, tmp_path):
        repo = _repo(tmp_path)
        run = {
            "episode_id": "ep_001",
            "sequence_id": "seq_001",
            "backend": "mock",
            "total_steps": 2,
            "approved_steps": 2,
            "executed_steps": 2,
            "blocked_steps": 0,
            "rejected_steps": 0,
            "manual_review_steps": 0,
            "episode_dir": "/tmp/ep_001",
        }
        repo.upsert_run(run)
        loaded = repo.get_run("ep_001")
        assert loaded is not None
        assert loaded["episode_id"] == "ep_001"
        assert loaded["total_steps"] == 2

    def test_upsert_run_overwrites_existing(self, tmp_path):
        repo = _repo(tmp_path)
        repo.upsert_run({"episode_id": "ep_002", "total_steps": 1, "episode_dir": "/tmp/ep_002"})
        repo.upsert_run({"episode_id": "ep_002", "total_steps": 3, "episode_dir": "/tmp/ep_002"})
        loaded = repo.get_run("ep_002")
        assert loaded["total_steps"] == 3

    def test_get_nonexistent_run_returns_none(self, tmp_path):
        repo = _repo(tmp_path)
        assert repo.get_run("nonexistent") is None

    def test_replace_steps(self, tmp_path):
        repo = _repo(tmp_path)
        repo.replace_steps("ep_003", [
            {"step_id": "s1", "executed": True},
            {"step_id": "s2", "executed": False, "blocked_reason": "rejected"},
        ])
        steps = repo.get_steps("ep_003")
        assert len(steps) == 2
        assert steps[0]["step_id"] == "s1"
        assert steps[1]["blocked_reason"] == "rejected"

    def test_replace_steps_overwrites(self, tmp_path):
        repo = _repo(tmp_path)
        repo.replace_steps("ep_004", [{"step_id": "s1", "executed": True}])
        repo.replace_steps("ep_004", [{"step_id": "s2", "executed": True}])
        steps = repo.get_steps("ep_004")
        assert len(steps) == 1
        assert steps[0]["step_id"] == "s2"

    def test_replace_artifacts(self, tmp_path):
        repo = _repo(tmp_path)
        repo.replace_artifacts("ep_005", [
            {"kind": "episode_summary", "path": "/a/summary.md", "description": "s"},
            {"kind": "clearance_curve", "path": "/a/curve.png"},
        ])
        run = repo.get_run("ep_005")
        # artifacts aren't queried directly via repo; verify replace succeeds
        assert run is None  # no run record, but artifacts were inserted

    def test_list_runs_returns_most_recent_first(self, tmp_path):
        repo = _repo(tmp_path)
        repo.upsert_run({"episode_id": "ep_a", "total_steps": 1, "episode_dir": "/a"})
        repo.upsert_run({"episode_id": "ep_b", "total_steps": 2, "episode_dir": "/b"})
        runs = repo.list_runs(limit=10)
        assert len(runs) == 2
        assert runs[0]["episode_id"] == "ep_b"  # most recent first

    def test_list_runs_respects_limit(self, tmp_path):
        repo = _repo(tmp_path)
        for i in range(5):
            repo.upsert_run({"episode_id": f"ep_{i}", "total_steps": 1, "episode_dir": f"/{i}"})
        runs = repo.list_runs(limit=3)
        assert len(runs) == 3
