from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from diagnostics.geometry.urdf_calibration import calibrate_task_geometry, parse_urdf_collision_boxes


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"
URDF = ROOT / "assets" / "robots" / "mock_realman_6dof" / "robot.urdf"


def test_parse_urdf_collision_boxes_extracts_link_dimensions():
    boxes = parse_urdf_collision_boxes(URDF)

    assert boxes["link_3"]["origin_xyz"] == [0.14, 0.0, 0.0]
    assert boxes["link_3"]["size"] == [0.28, 0.04, 0.04]
    assert boxes["link_4"]["origin_xyz"] == [0.1, 0.0, 0.0]
    assert boxes["link_4"]["size"] == [0.2, 0.035, 0.035]


def test_calibrate_task_geometry_compares_mock_and_pybullet_geometry():
    pytest.importorskip("pybullet")

    report = calibrate_task_geometry(BENCH / "mid_trajectory_collision_001")

    assert report["task_id"] == "mid_trajectory_collision_001"
    assert report["worst_step"] == 5
    assert report["pybullet"]["closest_link"] == "link_3"
    assert report["pybullet"]["closest_obstacle"] == "sphere_mid"
    assert report["mock_at_pybullet_worst_step"]["closest_link"] is not None
    assert isinstance(report["mock_at_pybullet_worst_step"]["clearance"], float)
    assert report["mock_overall_worst"]["step"] == 10
    assert report["mock_overall_worst"]["closest_link"] == "link_4"
    assert report["mock_overall_worst"]["clearance"] < 0
    assert "link_3" in report["link_calibration"]
    assert "link_4" in report["link_calibration"]
    assert report["link_calibration"]["link_3"]["urdf_length"] == pytest.approx(0.28)
    assert report["link_calibration"]["link_4"]["urdf_length"] == pytest.approx(0.2)
    assert report["conclusion"]["category"] in {
        "kinematic_model_mismatch",
        "geometry_size_mismatch",
        "calibrated",
    }
    assert report["recommendation"]


def test_calibrate_task_geometry_is_json_serializable():
    pytest.importorskip("pybullet")

    report = calibrate_task_geometry(BENCH / "multi_obstacle_clearance_001")

    encoded = json.dumps(report)
    decoded = json.loads(encoded)
    assert decoded["task_id"] == "multi_obstacle_clearance_001"


def test_calibrate_urdf_geometry_cli_writes_json(tmp_path):
    pytest.importorskip("pybullet")
    output_path = tmp_path / "calibration.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.calibrate_urdf_geometry",
            "--task",
            str(BENCH / "mid_trajectory_collision_001"),
            "--output-json",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "URDF Calibration" in completed.stdout
    assert "mid_trajectory_collision_001" in completed.stdout
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["pybullet"]["closest_link"] == "link_3"
