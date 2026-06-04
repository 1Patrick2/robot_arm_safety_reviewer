"""Deterministic simplified 6-DOF forward kinematics.

This is not a calibrated RealMan kinematic model. It is a mock serial chain
used to validate the safety review pipeline before a URDF/PyBullet/SDK backend
is available.
"""

from __future__ import annotations

import math

from .models import Point3D, RobotModel


def forward_kinematics_6dof(robot: RobotModel, joints: tuple[float, ...] | list[float]) -> list[Point3D]:
    """Return base plus six joint/end-effector points for a mock serial chain.

    Stage 1 currently supports identity base orientation only; base_orientation
    is parsed for future compatibility with real robot snapshots.
    """

    joint_values = tuple(float(item) for item in joints)
    if len(joint_values) != 6:
        raise ValueError("6-DOF forward kinematics requires six joint values")
    if len(robot.link_lengths) != 6:
        raise ValueError("robot.link_lengths must contain six lengths")

    x, y, z = robot.base_position
    points: list[Point3D] = [(round(x, 6), round(y, 6), round(z, 6))]
    yaw = joint_values[0]
    pitch = 0.0

    for index, length in enumerate(robot.link_lengths):
        if index == 0:
            z += length
        else:
            joint = joint_values[index]
            if index in {1, 2}:
                pitch += joint
            else:
                yaw += joint * 0.35
                pitch += joint * 0.2
            x += length * math.cos(pitch) * math.cos(yaw)
            y += length * math.cos(pitch) * math.sin(yaw)
            z += length * math.sin(pitch)
        points.append((round(x, 6), round(y, 6), round(z, 6)))

    return points
