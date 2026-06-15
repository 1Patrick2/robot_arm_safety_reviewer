from pathlib import Path

from application.metrics_service import (
    MetricsIngestRequest,
    MetricsListRunsRequest,
    MetricsShowRunRequest,
    metrics_ingest_episode,
    metrics_list_runs,
    metrics_show_run,
)
from application.sandbox_service import SandboxRunRequest, run_sandbox

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "policy_sequences"
BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"


def _sandbox_episode_dir(tmp_path, name: str = "sandbox") -> Path:
    result = run_sandbox(
        SandboxRunRequest(
            sequence_path=SAMPLES / "simple_safe_sequence.json",
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            output_root=tmp_path / name,
        )
    )
    return result.sequence_runtime_result.episode_dir


class TestMetricsIngest:
    def test_ingest_returns_summary(self, tmp_path):
        ep_dir = _sandbox_episode_dir(tmp_path)
        result = metrics_ingest_episode(
            MetricsIngestRequest(episode_dir=ep_dir, db_path=tmp_path / "test.db")
        )
        d = result.to_dict()
        assert d["total_steps"] == 2
        assert d["approved_steps"] == 2
        assert d["artifact_count"] == 3

    def test_ingest_to_app_result(self, tmp_path):
        ep_dir = _sandbox_episode_dir(tmp_path)
        result = metrics_ingest_episode(
            MetricsIngestRequest(episode_dir=ep_dir, db_path=tmp_path / "test.db")
        )
        app = result.to_app_result()
        assert app.ok is True
        assert app.mode == "metrics_ingest"


class TestMetricsListRuns:
    def test_list_returns_ingested_runs(self, tmp_path):
        db_path = tmp_path / "test.db"
        ep_dir = _sandbox_episode_dir(tmp_path)
        metrics_ingest_episode(MetricsIngestRequest(episode_dir=ep_dir, db_path=db_path))

        result = metrics_list_runs(MetricsListRunsRequest(db_path=db_path))
        d = result.to_dict()
        assert d["count"] >= 1
        assert any(r["episode_id"] == ep_dir.name for r in d["runs"])


class TestMetricsShowRun:
    def test_show_returns_run_and_steps(self, tmp_path):
        db_path = tmp_path / "test.db"
        ep_dir = _sandbox_episode_dir(tmp_path)
        metrics_ingest_episode(MetricsIngestRequest(episode_dir=ep_dir, db_path=db_path))

        result = metrics_show_run(
            MetricsShowRunRequest(episode_id=ep_dir.name, db_path=db_path)
        )
        d = result.to_dict()
        assert d["run"] is not None
        assert d["step_count"] == 2
        assert d["run"]["episode_id"] == ep_dir.name

    def test_show_nonexistent_run(self, tmp_path):
        result = metrics_show_run(
            MetricsShowRunRequest(episode_id="nonexistent", db_path=tmp_path / "test.db")
        )
        d = result.to_dict()
        assert d["run"] is None
        assert d["step_count"] == 0
