from pathlib import Path

import pytest

from gateway.safety_gate import review_only
from reports.report_writer import build_markdown_report
from robot.safety.evaluator import evaluate_joint_command_with_metadata
from robot.safety.models import JointCommand, Scene


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_mock_backend_log_records_diagnostic_metadata(tmp_path):
    task_dir = BENCH / "simple_joint_move_001"

    outcome = review_only(
        task_dir / "scene.json",
        task_dir / "command.json",
        backend_name="mock",
        log_dir=tmp_path,
    )

    metadata = outcome.execution_log["review_backend"]
    assert metadata["name"] == "mock"
    assert metadata["model_version"] == "mock_geometry_v1"
    assert metadata["collision_method"] == "segment_sphere_clearance"


def test_evaluator_returns_explicit_backend_metadata_without_mutating_backend():
    task_dir = BENCH / "simple_joint_move_001"
    scene = Scene.from_json(task_dir / "scene.json")
    command = JointCommand.from_json(task_dir / "command.json")

    class RecordingBackend:
        name = "recording"

        def replay_joint_trajectory(self, *, scene, trajectory):
            from robot.backends.base import BackendReviewResult

            return BackendReviewResult(
                backend_name=self.name,
                collision_free=True,
                min_clearance=0.2,
                closest_robot_link="link_1",
                closest_obstacle="sphere_clear",
                worst_step=0,
                violations=(),
                metadata={"model_version": "recording_v1", "collision_method": "test_clearance"},
            )

    backend = RecordingBackend()

    outcome = evaluate_joint_command_with_metadata(scene, command, backend=backend)

    assert outcome.safety_result.decision == "approve"
    assert outcome.backend_metadata == {
        "name": "recording",
        "model_version": "recording_v1",
        "collision_method": "test_clearance",
    }
    assert not hasattr(backend, "last_review_metadata")


def test_pybullet_backend_log_records_diagnostic_metadata(tmp_path):
    pytest.importorskip("pybullet")
    task_dir = BENCH / "simple_joint_move_001"

    outcome = review_only(
        task_dir / "scene.json",
        task_dir / "command.json",
        backend_name="pybullet",
        log_dir=tmp_path,
    )

    metadata = outcome.execution_log["review_backend"]
    assert metadata["name"] == "pybullet"
    assert metadata["mode"] == "DIRECT"
    assert metadata["collision_method"] == "pybullet_closest_points_sphere_collision"
    assert metadata["fidelity"] == "collision_geometry"
    assert metadata["closest_point_search_distance"] == pytest.approx(0.30)
    assert metadata["checked_links"] == []
    assert "mock_realman_6dof" in metadata["urdf_path"]
    assert "closest-point queries" in metadata["notes"]


def test_markdown_report_includes_review_backend_section(tmp_path):
    pytest.importorskip("pybullet")
    task_dir = BENCH / "simple_joint_move_001"
    outcome = review_only(
        task_dir / "scene.json",
        task_dir / "command.json",
        backend_name="pybullet",
        log_dir=tmp_path,
    )

    markdown = build_markdown_report(outcome.execution_log)

    assert "## Review Backend" in markdown
    assert "- Backend: `pybullet`" in markdown
    assert "- Mode: `DIRECT`" in markdown
    assert "- Collision method: `pybullet_closest_points_sphere_collision`" in markdown
    assert "- Fidelity: `collision_geometry`" in markdown
