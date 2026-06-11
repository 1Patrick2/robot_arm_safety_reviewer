"""Link-sphere clearance checks for the Stage 1 safety gate.
把每个机械臂 link 看成一段线段加半径，也就是 capsule-like link；障碍物是 sphere。计算线段到球心的距离，再减去 sphere radius 和 link radius，得到 signed clearance
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .kinematics import forward_kinematics_6dof
from .models import Point3D, RobotModel, SphereObstacle, Violation

# 姿态碰撞检查结果类
@dataclass(frozen=True)
class StateCollisionResult:
    collision_free: bool
    min_clearance: float
    closest_robot_link: str | None
    closest_obstacle: str | None
    violations: tuple[Violation, ...]

# 轨迹碰撞检查结果类
@dataclass(frozen=True)
class TrajectoryCollisionResult:
    collision_free: bool
    min_clearance: float
    closest_robot_link: str | None
    closest_obstacle: str | None
    worst_step: int | None # 中间碰撞的索引量
    violations: tuple[Violation, ...]

# 计算3D点到线段的最短距离，P1,P2是线段的两个端点，point是球心。返回值是点到线段的欧几里得距离。
def distance_segment_to_point(p1: Point3D, p2: Point3D, point: Point3D) -> float:
    """Return Euclidean distance from a 3D point to a line segment."""

    sx, sy, sz = p1
    ex, ey, ez = p2
    px, py, pz = point
    vx, vy, vz = ex - sx, ey - sy, ez - sz
    wx, wy, wz = px - sx, py - sy, pz - sz
    length_sq = vx * vx + vy * vy + vz * vz
    if length_sq == 0.0:
        return _distance(p1, point)
    t = max(0.0, min(1.0, (wx * vx + wy * vy + wz * vz) / length_sq))
    projection = (sx + t * vx, sy + t * vy, sz + t * vz)
    return _distance(projection, point)

# 计算线段到球的 signed clearance，等于点到线段距离减去球半径和 link 半径。正值表示安全距离，负值表示碰撞。
def segment_sphere_clearance(
    p1: Point3D,
    p2: Point3D,
    sphere: SphereObstacle,
    link_radius: float,
) -> float:
    """Return signed clearance between a capsule-like link segment and sphere."""

    return distance_segment_to_point(p1, p2, sphere.position) - sphere.radius - link_radius

# 检查机械臂姿态是否与障碍物碰撞
'''for 每个 link segment:
    for 每个 obstacle:
        算 clearance
        更新 min_clearance / closest link / closest obstacle
        如果 clearance < 0:
            添加 environment_collision violation
最后返回该姿态的collision result'''
def check_state_collision(
    points: list[Point3D],
    obstacles: tuple[SphereObstacle, ...],
    link_radius: float,
) -> StateCollisionResult:
    """Check one robot posture against sphere obstacles."""

    if not obstacles:
        return StateCollisionResult(True, 999.0, None, None, ())

    min_clearance = math.inf
    closest_link: str | None = None
    closest_obstacle: str | None = None
    violations: list[Violation] = []

    for link_index, (start, end) in enumerate(zip(points, points[1:]), start=1):
        link_name = f"link_{link_index}"
        for obstacle in obstacles:
            clearance = segment_sphere_clearance(start, end, obstacle, link_radius)
            if clearance < min_clearance:
                min_clearance = clearance
                closest_link = link_name
                closest_obstacle = obstacle.obstacle_id
            if clearance < 0.0:
                violations.append(
                    Violation(
                        type="environment_collision",
                        message=f"{link_name} collides with {obstacle.obstacle_id}.",
                        object=obstacle.obstacle_id,
                        link=link_name,
                        clearance=round(clearance, 6),
                    )
                )

    return StateCollisionResult(
        collision_free=not violations,
        min_clearance=round(min_clearance, 6),
        closest_robot_link=closest_link,
        closest_obstacle=closest_obstacle,
        violations=tuple(violations),
    )

'''检查整条轨迹的碰撞，返回最小 clearance 的 step 和 link / obstacle 信息，以及所有 violation
for step, joints in trajectory:
    points = forward_kinematics_6dof(robot, joints)
    result = check_state_collision(points, obstacles, robot.link_radius)
    if result.min_clearance < global_min_clearance:
        更新全局最小 clearance
        更新 closest link / closest obstacle
        更新 worst_step
        保存该 step 的 violations
这里是只保存最坏 step 的 violation，因为我们只关心轨迹中最危险的点。最后返回整个轨迹的 collision result'''
def check_trajectory_collision(
    trajectory: list[tuple[float, ...]],
    robot: RobotModel,
    obstacles: tuple[SphereObstacle, ...],
) -> TrajectoryCollisionResult:
    """Check every interpolated joint state and return the worst clearance."""

    if not obstacles:
        return TrajectoryCollisionResult(True, 999.0, None, None, None, ())

    min_clearance = math.inf
    closest_link: str | None = None
    closest_obstacle: str | None = None
    worst_step: int | None = None
    worst_violations: tuple[Violation, ...] = ()

    for step, joints in enumerate(trajectory):
        result = check_state_collision(forward_kinematics_6dof(robot, joints), obstacles, robot.link_radius)
        if result.min_clearance < min_clearance:
            min_clearance = result.min_clearance
            closest_link = result.closest_robot_link
            closest_obstacle = result.closest_obstacle
            worst_step = step
            worst_violations = tuple(
                Violation(
                    type=violation.type,
                    message=violation.message,
                    object=violation.object,
                    link=violation.link,
                    step=step,
                    clearance=violation.clearance,
                )
                for violation in result.violations
            )

    return TrajectoryCollisionResult(
        collision_free=not worst_violations,
        min_clearance=round(min_clearance, 6),
        closest_robot_link=closest_link,
        closest_obstacle=closest_obstacle,
        worst_step=worst_step,
        violations=worst_violations,
    )


def _distance(first: Point3D, second: Point3D) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))
