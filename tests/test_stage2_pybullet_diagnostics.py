from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from sim.pybullet_diagnostics import diagnose_task_geometry


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_diagnose_task_geometry_returns_structured_worst_pair():
    pytest.importorskip("pybullet")

    diagnostic = diagnose_task_geometry(BENCH / "mid_trajectory_collision_001")

    assert diagnostic["task_id"] == "mid_trajectory_collision_001"
    assert diagnostic["backend"] == "pybullet"
    assert diagnostic["collision_method"] == "pybullet_closest_points_sphere_collision"
    assert diagnostic["checked_links"] == ["link_1", "link_2", "link_3", "link_4", "link_5", "link_6"]
    assert diagnostic["closest_point_search_distance"] == pytest.approx(0.30)
    assert diagnostic["steps"]

    worst_pair = diagnostic["worst_pair"]
    assert worst_pair["step"] is not None
    assert worst_pair["robot_link"] is not None
    assert worst_pair["obstacle"] == "sphere_mid"
    assert isinstance(worst_pair["clearance"], float)


def test_diagnose_task_geometry_records_link_poses_and_closest_points():
    pytest.importorskip("pybullet")

    diagnostic = diagnose_task_geometry(BENCH / "obstacle_collision_001")

    first_step = diagnostic["steps"][0]
    assert first_step["step"] == 0
    assert len(first_step["joints"]) == 6
    assert "link_3" in first_step["link_poses"]
    assert len(first_step["link_poses"]["link_3"]["position"]) == 3
    assert first_step["closest_points"]
    assert {
        "step",
        "robot_link",
        "obstacle",
        "clearance",
        "position_on_robot",
        "position_on_obstacle",
    } <= set(first_step["closest_points"][0])


def test_diagnose_task_geometry_is_json_serializable():
    pytest.importorskip("pybullet")

    diagnostic = diagnose_task_geometry(BENCH / "near_miss_clearance_001")

    encoded = json.dumps(diagnostic)
    decoded = json.loads(encoded)
    assert decoded["task_id"] == "near_miss_clearance_001"


def test_diagnose_backend_geometry_cli_writes_json(tmp_path):
    pytest.importorskip("pybullet")
    output_path = tmp_path / "geometry.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.diagnose_backend_geometry",
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

    assert "Geometry Diagnostics" in completed.stdout
    assert "mid_trajectory_collision_001" in completed.stdout
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["worst_pair"]["obstacle"] == "sphere_mid"
