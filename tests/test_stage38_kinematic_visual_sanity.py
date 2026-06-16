from pathlib import Path

import pytest

from robot_safety.kinematics import forward_kinematics_6dof
from robot_safety.models import RobotModel

MOCK_ROBOT = RobotModel(
    robot_id="mock",
    model_type="mock_6dof",
    model_version="1.0",
    joint_names=("j1", "j2", "j3", "j4", "j5", "j6"),
    joint_limits=(),
    link_lengths=(0.18, 0.32, 0.28, 0.2, 0.14, 0.1),
    link_radius=0.03,
)


class TestFKChainCorrectness:
    def test_all_zero_joints_returns_seven_points(self):
        """base + 6 links = 7 points."""
        fk = forward_kinematics_6dof(MOCK_ROBOT, [0, 0, 0, 0, 0, 0])
        assert len(fk) == 7

    def test_all_zero_joints_starts_at_origin(self):
        fk = forward_kinematics_6dof(MOCK_ROBOT, [0, 0, 0, 0, 0, 0])
        assert fk[0] == (0.0, 0.0, 0.0)

    def test_j1_positive_moves_in_x_and_y(self):
        """Rotating j1 (yaw) should move the end-effector in the x-y plane."""
        zero_fk = forward_kinematics_6dof(MOCK_ROBOT, [0, 0, 0, 0, 0, 0])
        j1_fk = forward_kinematics_6dof(MOCK_ROBOT, [0.5, 0, 0, 0, 0, 0])
        assert j1_fk[-1][0] != zero_fk[-1][0]
        assert j1_fk[-1][1] != zero_fk[-1][1]

    def test_j2_positive_changes_z(self):
        """Rotating j2 (pitch) should change the end-effector height."""
        zero_fk = forward_kinematics_6dof(MOCK_ROBOT, [0, 0, 0, 0, 0, 0])
        j2_fk = forward_kinematics_6dof(MOCK_ROBOT, [0, 0.5, 0, 0, 0, 0])
        assert j2_fk[-1][2] != zero_fk[-1][2]

    def test_link_0_is_vertical(self):
        """The first link (j0) is vertical in the mock model."""
        fk = forward_kinematics_6dof(MOCK_ROBOT, [0, 0, 0, 0, 0, 0])
        dz = fk[1][2] - fk[0][2]
        assert abs(dz - MOCK_ROBOT.link_lengths[0]) < 0.001

    def test_positive_j2_lifts_end_effector(self):
        """Rotating j2 positive should increase end-effector z more than zero case."""
        zero_fk = forward_kinematics_6dof(MOCK_ROBOT, [0, 0, 0, 0, 0, 0])
        j2_fk = forward_kinematics_6dof(MOCK_ROBOT, [0, 0.5, 0, 0, 0, 0])
        assert j2_fk[-1][2] > zero_fk[-1][2]
