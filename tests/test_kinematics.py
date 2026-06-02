from pathlib import Path

from robot_arm.kinematics import forward_kinematics_3d, sample_ik_candidates
from robot_arm.models import RobotArmScene

ROOT = Path(__file__).resolve().parents[1]


def test_forward_kinematics_outputs_five_points_for_four_dof_arm():
    scene = RobotArmScene.from_json(ROOT / "bench/robot_arm/simple_3d_reach_001/scene.json")

    points = forward_kinematics_3d(scene.robot, (0.0, 0.0, 0.0, 0.0))

    assert len(points) == 5
    assert points[0] == (0.0, 0.0, 0.0)
    assert points[1] == (0.0, 0.0, 0.25)
    assert points[-1][0] > 1.6


def test_sampling_ik_finds_reachable_target_within_tolerance():
    scene = RobotArmScene.from_json(ROOT / "bench/robot_arm/simple_3d_reach_001/scene.json")

    candidates = sample_ik_candidates(scene.robot, scene.target)

    assert candidates
    assert candidates[0][1] <= scene.target.tolerance


def test_sampling_ik_marks_unreachable_target_above_tolerance():
    scene = RobotArmScene.from_json(ROOT / "bench/robot_arm/unreachable_target_001/scene.json")

    candidates = sample_ik_candidates(scene.robot, scene.target)

    assert candidates
    assert candidates[0][1] > scene.target.tolerance
