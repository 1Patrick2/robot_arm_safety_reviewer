"""Joint-space trajectory helpers."""

from __future__ import annotations


def interpolate_joint_trajectory(
    current_joints: tuple[float, ...] | list[float],
    target_joints: tuple[float, ...] | list[float],
    steps: int,
) -> list[tuple[float, ...]]:
    """Linearly interpolate a deterministic joint trajectory including endpoints."""

    # 检查维度
    current = tuple(float(item) for item in current_joints)
    target = tuple(float(item) for item in target_joints)
    if len(current) != len(target):
        raise ValueError("current_joints and target_joints must have the same dimension")
    if steps < 2:
        raise ValueError("steps must be at least 2")

    # 简单线性插值，生成一个包含 steps 个点的轨迹，从 current 到 target，均匀分布在两者之间。每个点都是一个关节状态的 tuple。
    trajectory = []
    for index in range(steps):
        ratio = index / (steps - 1)
        trajectory.append(tuple(start + (end - start) * ratio for start, end in zip(current, target)))
    return trajectory

# 返回每个关节运动幅度的最大值
def compute_max_joint_delta(
    current_joints: tuple[float, ...] | list[float],
    target_joints: tuple[float, ...] | list[float],
) -> float:
    """Return the maximum absolute per-joint motion."""

    current = tuple(float(item) for item in current_joints)
    target = tuple(float(item) for item in target_joints)
    if len(current) != len(target):
        raise ValueError("current_joints and target_joints must have the same dimension")
    return max((abs(end - start) for start, end in zip(current, target)), default=0.0)

