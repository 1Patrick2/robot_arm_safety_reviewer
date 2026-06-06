from pathlib import Path

import pytest

from gateway.safety_gate import review_only
from reports.report_writer import build_markdown_report


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
