import json
from pathlib import Path

import pytest

from diagnostics.storage.episode_ingest import (
    build_artifact_records,
    build_run_record,
    build_step_records,
    ingest_episode,
)
from diagnostics.storage.repository import RuntimeMetricsRepository
from diagnostics.storage.schema import init_runtime_db

SAMPLES = Path(__file__).resolve().parents[1] / "bench" / "samples" / "policy_sequences"
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

    def test_worst_step_fields(self, tmp_path):
        """Verify worst_sequence_step_index and backend_worst_step are populated."""
        ep_dir = _write_episode(tmp_path / "ep_worst", steps=[
            {
                "step_id": "s1", "step_index": 1,
                "safety_result": {"decision": "approve", "risk_level": "low", "min_clearance": 0.05, "worst_step": 3},
                "executed": True,
            },
            {
                "step_id": "s2", "step_index": 2,
                "safety_result": {"decision": "approve", "risk_level": "low", "min_clearance": 0.02, "worst_step": 7},
                "executed": True,
            },
            {
                "step_id": "s3", "step_index": 3,
                "safety_result": {"decision": "approve", "risk_level": "low", "min_clearance": 0.10, "worst_step": 1},
                "executed": True,
            },
        ])
        record = build_run_record(ep_dir)
        # worst sequence step is step 2 (clearance=0.02)
        assert record["worst_sequence_step_index"] == 2
        # backend worst_step for that step is 7
        assert record["backend_worst_step"] == 7
        # legacy worst_step preserved
        assert record["worst_step"] == 7


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
        assert summary["artifact_count"] == 4

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


def _write_episode(episode_dir: Path, *, steps: list[dict]) -> Path:
    """Write a minimal episode with metadata.json and steps.jsonl."""
    episode_dir.mkdir(parents=True, exist_ok=True)
    (episode_dir / "metadata.json").write_text(
        json.dumps({"episode_id": episode_dir.name, "backend": "mock", "robot": "mock_realman"}),
        encoding="utf-8",
    )
    with (episode_dir / "steps.jsonl").open("w", encoding="utf-8") as f:
        for s in steps:
            f.write(json.dumps(s) + "\n")
    return episode_dir


class TestBuildRunRecordReject:
    def test_reject_episode_counts(self, tmp_path):
        """Ingest an episode with a rejected step."""
        ep_dir = _write_episode(tmp_path / "ep_reject", steps=[
            {
                "step_id": "s1",
                "safety_result": {"decision": "reject", "risk_level": "high", "min_clearance": -0.1, "worst_step": 0},
                "executed": False,
                "blocked_reason": "rejected_by_safety_gate",
            },
        ])
        record = build_run_record(ep_dir)
        assert record["total_steps"] == 1
        assert record["approved_steps"] == 0
        assert record["executed_steps"] == 0
        assert record["blocked_steps"] == 1
        assert record["rejected_steps"] == 1
        assert record["manual_review_steps"] == 0

    def test_manual_review_episode_counts(self, tmp_path):
        ep_dir = _write_episode(tmp_path / "ep_manual", steps=[
            {
                "step_id": "s1",
                "safety_result": {"decision": "manual_review", "risk_level": "medium", "min_clearance": 0.01},
                "executed": False,
                "blocked_reason": "manual_review_required",
            },
        ])
        record = build_run_record(ep_dir)
        assert record["total_steps"] == 1
        assert record["approved_steps"] == 0
        assert record["executed_steps"] == 0
        assert record["blocked_steps"] == 1
        assert record["rejected_steps"] == 0
        assert record["manual_review_steps"] == 1

    def test_approved_but_execution_failed_counts_as_blocked(self, tmp_path):
        """Approved step where robot execution fails: blocked_steps should count it."""
        ep_dir = _write_episode(tmp_path / "ep_fail", steps=[
            {
                "step_id": "s1",
                "safety_result": {"decision": "approve", "risk_level": "low", "min_clearance": 0.05},
                "executed": False,
                "blocked_reason": None,
            },
        ])
        record = build_run_record(ep_dir)
        assert record["approved_steps"] == 1
        assert record["executed_steps"] == 0
        # blocked matches runtime definition: not step.executed
        assert record["blocked_steps"] == 1

    def test_zero_clearance_boundary(self, tmp_path):
        """min_clearance=0.0 and worst_step=0 are meaningful values, not missing."""
        ep_dir = _write_episode(tmp_path / "ep_boundary", steps=[
            {
                "step_id": "s1",
                "safety_result": {"decision": "manual_review", "risk_level": "medium", "min_clearance": 0.0, "worst_step": 0},
                "executed": False,
                "blocked_reason": "manual_review_required",
            },
        ])
        record = build_run_record(ep_dir)
        assert record["min_clearance"] == 0.0
        assert record["worst_step"] == 0


class TestBuildStepRecordsCorrupt:
    def test_missing_steps_jsonl_raises(self, tmp_path):
        ep_dir = tmp_path / "incomplete_episode"
        ep_dir.mkdir()
        (ep_dir / "metadata.json").write_text('{"episode_id": "incomplete"}', encoding="utf-8")
        with pytest.raises(FileNotFoundError, match="steps.jsonl"):
            build_step_records(ep_dir)

    def test_missing_steps_jsonl_blocks_ingest(self, tmp_path):
        ep_dir = tmp_path / "incomplete_episode"
        ep_dir.mkdir()
        (ep_dir / "metadata.json").write_text('{"episode_id": "incomplete"}', encoding="utf-8")
        with pytest.raises(FileNotFoundError, match="steps.jsonl"):
            ingest_episode(tmp_path / "metrics.db", ep_dir)
