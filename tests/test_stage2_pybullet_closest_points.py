from pathlib import Path

import pytest

from robot_safety.models import JointCommand, Scene
from robot_safety.trajectory import interpolate_joint_trajectory
from sim.pybullet_backend import PyBulletBackend


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def _review_task(task_id: str, *, backend: PyBulletBackend | None = None):
    task_dir = BENCH / task_id
    scene = Scene.from_json(task_dir / "scene.json")
    command = JointCommand.from_json(task_dir / "command.json")
    trajectory = interpolate_joint_trajectory(
        command.current_joints,
        command.target_joints,
        scene.safety_config.num_interpolation_steps,
    )
    return (backend or PyBulletBackend()).replay_joint_trajectory(scene=scene, trajectory=trajectory)


def test_pybullet_backend_uses_closest_points_metadata():
    pytest.importorskip("pybullet")

    result = _review_task("obstacle_collision_001")

    assert result.metadata["collision_method"] == "pybullet_closest_points_sphere_collision"
    assert result.metadata["fidelity"] == "collision_geometry"
    assert result.metadata["closest_point_search_distance"] == pytest.approx(0.30)
    assert result.metadata["checked_links"]


def test_closest_points_simple_joint_move_stays_clear():
    pytest.importorskip("pybullet")

    result = _review_task("simple_joint_move_001")

    assert result.collision_free is True
    assert result.min_clearance == 999.0
    assert result.closest_robot_link is None
    assert result.closest_obstacle is None
    assert result.violations == ()


def test_closest_points_obstacle_collision_rejects_geometry_overlap():
    pytest.importorskip("pybullet")

    result = _review_task("obstacle_collision_001")

    assert result.collision_free is False
    assert result.min_clearance < 0
    assert result.closest_obstacle == "sphere_01"
    assert result.closest_robot_link is not None
    assert result.worst_step == 0
    assert any(violation.type == "environment_collision" for violation in result.violations)


def test_closest_points_mid_trajectory_collision_has_meaningful_geometry_signal():
    pytest.importorskip("pybullet")

    result = _review_task("mid_trajectory_collision_001")

    assert result.min_clearance != 999.0
    assert result.closest_obstacle is not None
    assert result.closest_robot_link is not None
    assert result.worst_step is not None


def test_link_position_collision_method_remains_available():
    pytest.importorskip("pybullet")

    backend = PyBulletBackend(collision_method="link_position_sphere_clearance")

    result = _review_task("obstacle_collision_001", backend=backend)

    assert result.metadata["collision_method"] == "link_position_sphere_clearance"
    assert result.metadata["fidelity"] == "approximate"
