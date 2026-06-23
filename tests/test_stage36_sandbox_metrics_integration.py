from pathlib import Path

from application.sandbox_service import SandboxRunRequest, run_sandbox
from runtime_db.repository import RuntimeMetricsRepository

SAMPLES = Path(__file__).resolve().parents[1] / "bench" / "samples" / "policy_sequences"
BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"


class TestSandboxMetricsIntegration:
    def test_sandbox_with_metrics_db_auto_ingests(self, tmp_path):
        db_path = tmp_path / "metrics.db"
        result = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "simple_safe_sequence.json",
                scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path / "sandbox",
                metrics_db=db_path,
            )
        )

        # metrics ingest summary is returned
        assert result.metrics_ingest_summary is not None
        assert result.metrics_ingest_summary["total_steps"] == 2

        # data is actually in the database
        repo = RuntimeMetricsRepository(db_path)
        run = repo.get_run(result.sequence_runtime_result.episode_dir.name)
        assert run is not None
        steps = repo.get_steps(result.sequence_runtime_result.episode_dir.name)
        assert len(steps) == 2

    def test_sandbox_without_metrics_db_does_not_ingest(self, tmp_path):
        result = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "simple_safe_sequence.json",
                scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path / "sandbox",
            )
        )

        assert result.metrics_ingest_summary is None
