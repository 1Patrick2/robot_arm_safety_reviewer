from pathlib import Path

import json

from application.sandbox_service import SandboxRunRequest, run_sandbox

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "policy_sequences"
BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"


class TestRunSandbox:
    def test_produces_all_artifacts(self, tmp_path):
        result = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "simple_safe_sequence.json",
                scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path,
            )
        )

        assert result.sequence_runtime_result.total_steps == 2
        assert result.sequence_runtime_result.approved_steps == 2
        assert result.episode_summary_path.exists()
        assert result.clearance_curve_path.exists()
        assert result.trajectory_overview_path.exists()

        # artifacts are written inside the episode directory
        episode_dir = result.sequence_runtime_result.episode_dir
        assert result.episode_summary_path.parent == episode_dir
        assert result.clearance_curve_path.parent == episode_dir
        assert result.trajectory_overview_path.parent == episode_dir

    def test_multiple_runs_do_not_overwrite_artifacts(self, tmp_path):
        """Run sandbox twice with different scenes and verify each has its own artifacts."""
        result1 = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "simple_safe_sequence.json",
                scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path,
            )
        )
        result2 = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "simple_safe_sequence.json",
                scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path,
            )
        )

        # each run has its own episode dir
        ep1 = result1.sequence_runtime_result.episode_dir
        ep2 = result2.sequence_runtime_result.episode_dir
        assert ep1 != ep2

        # artifacts live in their respective episode dirs
        assert result1.episode_summary_path.parent == ep1
        assert result2.episode_summary_path.parent == ep2
        assert result1.clearance_curve_path.parent == ep1
        assert result2.clearance_curve_path.parent == ep2
        assert result1.trajectory_overview_path.parent == ep1
        assert result2.trajectory_overview_path.parent == ep2

        # both have their own copies (not overwritten)
        assert result1.episode_summary_path.exists()
        assert result2.episode_summary_path.exists()

    def test_to_dict_contains_all_paths(self, tmp_path):
        result = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "simple_safe_sequence.json",
                scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path,
            )
        )

        d = result.to_dict()
        assert d["total_steps"] == 2
        assert d["approved_steps"] == 2
        assert "episode_summary_path" in d
        assert "clearance_curve_path" in d
        assert "trajectory_overview_path" in d

    def test_to_app_result_contains_artifacts(self, tmp_path):
        result = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "simple_safe_sequence.json",
                scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path,
            )
        )

        app_result = result.to_app_result()
        assert app_result.ok is True
        assert app_result.mode == "sandbox_run"
        kinds = [a.kind for a in app_result.artifacts]
        assert "runtime_episode" in kinds
        assert "episode_summary" in kinds
        assert "clearance_curve" in kinds
        assert "trajectory_overview" in kinds

    def test_metadata_contains_run_mode(self, tmp_path):
        result = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "simple_safe_sequence.json",
                scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path,
            )
        )

        episode_dir = result.sequence_runtime_result.episode_dir
        meta_path = episode_dir / "metadata.json"
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["run_mode"] == "sandbox"
        assert meta["artifact_schema_version"] == "stage3.visual_sandbox.v1"
