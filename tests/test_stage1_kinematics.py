from pathlib import Path

from robot.safety.kinematics import forward_kinematics_6dof
from robot.safety.models import Scene

ROOT = Path(__file__).resolve().parents[1]


def test_forward_kinematics_outputs_seven_points_for_six_dof_arm():
    scene = Scene.from_json(ROOT / "bench/sim_robot_arm/simple_joint_move_001/scene.json")

    points = forward_kinematics_6dof(scene.robot, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    assert len(points) == 7
    assert points[0] == (0.0, 0.0, 0.0)
    assert all(len(point) == 3 for point in points)
    assert points[-1][0] > 1.0


def test_forward_kinematics_changes_when_joints_change():
    scene = Scene.from_json(ROOT / "bench/sim_robot_arm/simple_joint_move_001/scene.json")

    zero = forward_kinematics_6dof(scene.robot, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    moved = forward_kinematics_6dof(scene.robot, [0.4, -0.2, 0.3, 0.0, 0.0, 0.0])

    assert zero[-1] != moved[-1]

