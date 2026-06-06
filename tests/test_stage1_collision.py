from pathlib import Path

import pytest

from robot_safety.collision import (
    check_trajectory_collision,
    distance_segment_to_point,
    segment_sphere_clearance,
)
from robot_safety.models import Scene, SphereObstacle
from robot_safety.trajectory import interpolate_joint_trajectory

ROOT = Path(__file__).resolve().parents[1]


def test_distance_segment_to_point_returns_perpendicular_distance():
    distance = distance_segment_to_point((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 0.2, 0.0))

    assert distance == pytest.approx(0.2)


def test_segment_sphere_clearance_is_signed():
    sphere = SphereObstacle("sphere_01", (0.5, 0.0, 0.0), 0.2)

    clearance = segment_sphere_clearance((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), sphere, link_radius=0.05)

    assert clearance == pytest.approx(-0.25)


def test_check_trajectory_collision_reports_closest_link_and_obstacle():
    scene = Scene.from_json(ROOT / "bench/sim_robot_arm/obstacle_collision_001/scene.json")
    trajectory = interpolate_joint_trajectory([0.0] * 6, [0.0, 0.1, -0.1, 0.0, 0.0, 0.0], 5)

    result = check_trajectory_collision(trajectory, scene.robot, scene.obstacles)

    assert not result.collision_free
    assert result.min_clearance < 0.0
    assert result.closest_robot_link is not None
    assert result.closest_obstacle == "sphere_01"
    assert result.worst_step is not None

