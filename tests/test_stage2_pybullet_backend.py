from pathlib import Path

import pytest

from robot_safety.models import JointCommand, Scene
from robot_safety.trajectory import interpolate_joint_trajectory
from sim.pybullet_backend import PyBulletBackend


ROOT = Path(__file__).resolve().parents[1]


def test_pybullet_backend_loads_default_urdf():
    pytest.importorskip("pybullet")

    backend = PyBulletBackend()

    assert backend.name == "pybullet"
    assert backend.urdf_path.exists()


def test_pybullet_backend_returns_review_result_for_simple_scene():
    pytest.importorskip("pybullet")

    task_dir = ROOT / "bench" / "sim_robot_arm" / "simple_joint_move_001"
    scene = Scene.from_json(task_dir / "scene.json")
    command = JointCommand.from_json(task_dir / "command.json")
    trajectory = interpolate_joint_trajectory(
        command.current_joints,
        command.target_joints,
        scene.safety_config.num_interpolation_steps,
    )

    result = PyBulletBackend().replay_joint_trajectory(scene=scene, trajectory=trajectory)

    assert result.backend_name == "pybullet"
    assert result.collision_free is True
    assert result.min_clearance == 999.0
    assert result.closest_robot_link is None
    assert result.closest_obstacle is None
    assert result.violations == ()
    assert result.metadata["mode"] == "DIRECT"


def test_pybullet_backend_detects_sphere_collision_near_base_link():
    pytest.importorskip("pybullet")

    scene = Scene.from_dict(
        {
            "scene_id": "pybullet_base_collision_001",
            "robot": {
                "robot_id": "mock_realman_6dof",
                "model_type": "mock_6dof",
                "joint_names": ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"],
                "link_radius": 0.025,
                "link_lengths": [0.18, 0.32, 0.28, 0.2, 0.14, 0.1],
                "joint_limits": [
                    [-3.14, 3.14],
                    [-1.57, 1.57],
                    [-2.2, 2.2],
                    [-3.14, 3.14],
                    [-1.8, 1.8],
                    [-3.14, 3.14],
                ],
            },
            "obstacles": [
                {
                    "obstacle_id": "base_overlap",
                    "type": "sphere",
                    "position": [0.0, 0.0, 0.15],
                    "radius": 0.2,
                }
            ],
            "safety_config": {"min_clearance": 0.05},
        }
    )
    command = JointCommand.from_dict(
        {
            "command_id": "hold_position_001",
            "command_type": "joint_move",
            "current_joints": [0, 0, 0, 0, 0, 0],
            "target_joints": [0, 0, 0, 0, 0, 0],
            "speed": 0.2,
        }
    )
    trajectory = interpolate_joint_trajectory(
        command.current_joints,
        command.target_joints,
        scene.safety_config.num_interpolation_steps,
    )

    result = PyBulletBackend().replay_joint_trajectory(scene=scene, trajectory=trajectory)

    assert result.collision_free is False
    assert result.min_clearance < 0
    assert result.closest_obstacle == "base_overlap"
    assert result.closest_robot_link is not None
    assert result.worst_step == 0
    assert result.violations
