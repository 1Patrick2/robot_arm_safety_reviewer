import json
from pathlib import Path

import pytest

from reports.runtime_visual_report import write_trajectory_overview

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "policy_sequences"
BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"


def _run_sandbox(episode_root: Path) -> Path:
    from application.sandbox_service import SandboxRunRequest, run_sandbox
    result = run_sandbox(
        SandboxRunRequest(
            sequence_path=SAMPLES / "simple_safe_sequence.json",
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            output_root=episode_root,
        )
    )
    return result.sequence_runtime_result.episode_dir


class TestTrajectoryEvidenceData:
    def test_evidence_data_created_alongside_png(self, tmp_path):
        """write_trajectory_overview should also create trajectory_overview_data.json."""
        ep_dir = _run_sandbox(tmp_path / "sandbox")
        write_trajectory_overview(ep_dir)
        data_path = ep_dir / "trajectory_overview_data.json"
        assert data_path.exists()
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        assert "episode_id" in payload
        assert "steps" in payload
        assert len(payload["steps"]) > 0

    def test_each_step_contains_fk_points(self, tmp_path):
        ep_dir = _run_sandbox(tmp_path / "sandbox2")
        write_trajectory_overview(ep_dir)
        data_path = ep_dir / "trajectory_overview_data.json"
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        for step in payload["steps"]:
            assert "step_index" in step
            assert "decision" in step
            assert "target_joints" in step
            assert "fk_points" in step
            assert len(step["fk_points"]) == 7  # base + 6 links

    def test_evidence_data_robot_model_source(self, tmp_path):
        ep_dir = _run_sandbox(tmp_path / "sandbox3")
        write_trajectory_overview(ep_dir)
        data_path = ep_dir / "trajectory_overview_data.json"
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        assert payload.get("robot_model_source") in ("scene", "default_mock_fallback")
        assert payload.get("joint_units") == "rad"
