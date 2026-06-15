import json
from pathlib import Path

from runtime_db.episode_ingest import (
    build_artifact_records,
    build_run_record,
    build_step_records,
    ingest_episode,
)
from runtime_db.repository import RuntimeMetricsRepository
from runtime_db.schema import init_runtime_db

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "policy_sequences"
BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"


def _run_sandbox(episode_root: Path) -> Path:
    """Run a quick sandbox to produce a real episode dir for ingest testing."""
    from application.sandbox_service import SandboxRunRequest, run_sandbox  # noqa: PLC0415

    result = run_sandbox(
        SandboxRunRequest(
            sequence_path=SAMPLES / "simple_safe_sequence.json",
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            output_root=episode_root,
        )
    )
    return result.sequence_runtime_result.episode_dir


class TestBuildRunRecord:
    def test_extracts_run_record_from_sandbox_output(self, tmp_path):
        ep_dir = _run_sandbox(tmp_path / "sandbox")
        record = build_run_record(ep_dir)
        assert record["episode_id"] is not None
        assert record["total_steps"] == 2
        assert record["approved_steps"] == 2
        assert record["executed_steps"] == 2
        assert record["blocked_steps"] == 0
        assert record["min_clearance"] is not None


class TestBuildStepRecords:
    def test_extracts_steps(self, tmp_path):
        ep_dir = _run_sandbox(tmp_path / "sandbox")
        steps = build_step_records(ep_dir)
        assert len(steps) == 2
        for s in steps:
            assert "safety_result" in s
            assert "executed" in s


class TestBuildArtifactRecords:
    def test_detects_present_artifacts(self, tmp_path):
        ep_dir = _run_sandbox(tmp_path / "sandbox")
        artifacts = build_artifact_records(ep_dir)
        kinds = {a["kind"] for a in artifacts}
        assert "episode_summary" in kinds
        assert "clearance_curve" in kinds
        assert "trajectory_overview" in kinds


class TestIngestEpisode:
    def test_ingest_full_episode(self, tmp_path):
        ep_dir = _run_sandbox(tmp_path / "sandbox")
        db_path = tmp_path / "metrics.db"

        summary = ingest_episode(db_path, ep_dir)

        assert summary["episode_id"] is not None
        assert summary["total_steps"] == 2
        assert summary["artifact_count"] == 3

        # verify via repository
        repo = RuntimeMetricsRepository(db_path)
        run = repo.get_run(summary["episode_id"])
        assert run is not None
        assert run["total_steps"] == 2

        steps = repo.get_steps(summary["episode_id"])
        assert len(steps) == 2

    def test_reingest_does_not_duplicate_steps(self, tmp_path):
        ep_dir = _run_sandbox(tmp_path / "sandbox")
        db_path = tmp_path / "metrics.db"

        ingest_episode(db_path, ep_dir)
        ingest_episode(db_path, ep_dir)  # second time

        repo = RuntimeMetricsRepository(db_path)
        steps = repo.get_steps(ep_dir.name)
        assert len(steps) == 2  # still 2, not 4
