"""3D kinematics for a simplified 4-DOF robot arm."""

from __future__ import annotations

import math
from itertools import product

from robot_arm.models import RobotArm3D, Target

Point3D = tuple[float, float, float]
Joints4D = tuple[float, float, float, float]


def forward_kinematics_3d(robot: RobotArm3D, joints: Joints4D) -> list[Point3D]:
    """Return base, shoulder, elbow, wrist, and end-effector points."""

    base_height, upper_arm, forearm, wrist = robot.links
    yaw, shoulder_pitch, elbow_pitch, wrist_pitch = joints
    points: list[Point3D] = [(0.0, 0.0, 0.0), (0.0, 0.0, base_height)]
    radial = 0.0
    z = base_height
    angle = shoulder_pitch
    for length, delta in (
        (upper_arm, 0.0),
        (forearm, elbow_pitch),
        (wrist, wrist_pitch),
    ):
        angle += delta
        radial += length * math.cos(angle)
        z += length * math.sin(angle)
        points.append(
            (
                round(radial * math.cos(yaw), 6),
                round(radial * math.sin(yaw), 6),
                round(z, 6),
            )
        )
    return points


def sample_ik_candidates(
    robot: RobotArm3D,
    target: Target,
    *,
    samples_per_joint: int = 13,
    top_k: int = 40,
) -> list[tuple[Joints4D, float, list[Point3D]]]:
    """Sample joint space deterministically and return nearest candidates."""

    yaw_center = math.atan2(target.position[1], target.position[0])
    yaw_values = _values_around(yaw_center, robot.joint_limits[0], count=7, radius=0.35)
    shoulder_values = _linspace(robot.joint_limits[1], samples_per_joint)
    elbow_values = _linspace(robot.joint_limits[2], samples_per_joint)
    wrist_values = _linspace(robot.joint_limits[3], max(5, samples_per_joint // 2))

    candidates = []
    for joints in product(yaw_values, shoulder_values, elbow_values, wrist_values):
        joints4 = tuple(float(item) for item in joints)  # type: ignore[assignment]
        points = forward_kinematics_3d(robot, joints4)
        error = distance(points[-1], target.position)
        candidates.append((joints4, error, points))
    return sorted(candidates, key=lambda item: (item[1], _joint_distance(item[0], robot.current_joints)))[:top_k]


def check_joint_limits(joints: Joints4D, limits: tuple[tuple[float, float], ...]) -> bool:
    return all(lower <= value <= upper for value, (lower, upper) in zip(joints, limits))


def distance(first: Point3D, second: Point3D) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def _linspace(limit: tuple[float, float], count: int) -> list[float]:
    lower, upper = limit
    if count <= 1:
        return [(lower + upper) / 2.0]
    step = (upper - lower) / (count - 1)
    return [lower + step * index for index in range(count)]


def _values_around(center: float, limit: tuple[float, float], *, count: int, radius: float) -> list[float]:
    lower, upper = limit
    values = []
    for offset in _linspace((-radius, radius), count):
        value = min(max(center + offset, lower), upper)
        if value not in values:
            values.append(value)
    return values


def _joint_distance(first: Joints4D, second: Joints4D) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))
