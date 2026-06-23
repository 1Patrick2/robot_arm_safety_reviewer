import json
from pathlib import Path

import pytest

from diagnostics.report.runtime_visual_report import write_trajectory_overview

SAMPLES = Path(__file__).resolve().parents[1] / "bench" / "samples" / "policy_sequences"
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

    def test_joint_names_match_scene_robot(self, tmp_path):
        """joint_names in evidence data should use scene robot model's names."""
        from application.sandbox_service import SandboxRunRequest, run_sandbox
        ep_dir = _run_sandbox(tmp_path / "sandbox_jn")
        write_trajectory_overview(ep_dir)
        data_path = ep_dir / "trajectory_overview_data.json"
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        # The scene simple_joint_move_001 uses joint_names:
        # ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
        assert payload["joint_names"] == [
            "joint1", "joint2", "joint3", "joint4", "joint5", "joint6"
        ], f"got {payload['joint_names']}"

    def test_png_and_json_in_output_dir_when_specified(self, tmp_path):
        """When output_dir is given to write_trajectory_overview, both
        PNG and trajectory_overview_data.json should be in that directory."""
        ep_dir = _run_sandbox(tmp_path / "sandbox_out")
        out_dir = tmp_path / "custom_output"
        write_trajectory_overview(ep_dir, output_dir=out_dir)
        assert (out_dir / "trajectory_overview.png").exists()
        assert (out_dir / "trajectory_overview_data.json").exists()

    def test_obstacle_bounds_extend_auto_scale(self, tmp_path):
        """Evidence data should record obstacle bounds for scenes with obstacles."""
        from application.sandbox_service import SandboxRunRequest, run_sandbox
        BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"
        SAMPLES = Path(__file__).resolve().parents[1] / "bench" / "samples" / "policy_sequences"
        result = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "near_miss_sequence.json",
                scene_path=BENCH / "near_miss_clearance_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path / "sandbox_obs2",
                stop_on_block=False,
            )
        )
        ep_dir = result.sequence_runtime_result.episode_dir
        write_trajectory_overview(ep_dir)
        data_path = ep_dir / "trajectory_overview_data.json"
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        assert "obstacles" in payload
        obs = payload["obstacles"][0]
        assert "center" in obs
        assert "radius" in obs
        # Verify sphere_01 from near_miss_clearance_001 scene
        assert obs.get("obstacle_id") == "sphere_01"
        assert obs["center"] == [0.50, 0.095, 0.18]
