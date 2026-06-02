"""Collision checks for simplified 3D arm links and sphere obstacles."""

from __future__ import annotations

from robot_arm.kinematics import Point3D, distance
from robot_arm.models import SphereObstacle


def segment_sphere_collision(
    p1: Point3D,
    p2: Point3D,
    sphere: SphereObstacle,
    *,
    link_radius: float = 0.0,
) -> bool:
    return _point_segment_distance(sphere.center, p1, p2) <= sphere.radius + link_radius


def check_arm_collision(
    points: list[Point3D],
    obstacles: tuple[SphereObstacle, ...],
    *,
    link_radius: float = 0.0,
) -> tuple[bool, tuple[str, ...]]:
    collided: list[str] = []
    for obstacle in obstacles:
        for start, end in zip(points, points[1:]):
            if segment_sphere_collision(start, end, obstacle, link_radius=link_radius):
                collided.append(obstacle.obstacle_id)
                break
    return bool(collided), tuple(collided)


def minimum_obstacle_clearance(
    points: list[Point3D],
    obstacles: tuple[SphereObstacle, ...],
    *,
    link_radius: float = 0.0,
) -> float:
    if not obstacles:
        return 999.0
    minimum = 999.0
    for obstacle in obstacles:
        for start, end in zip(points, points[1:]):
            clearance = _point_segment_distance(obstacle.center, start, end) - obstacle.radius - link_radius
            minimum = min(minimum, clearance)
    return minimum


def _point_segment_distance(point: Point3D, start: Point3D, end: Point3D) -> float:
    sx, sy, sz = start
    ex, ey, ez = end
    px, py, pz = point
    vx, vy, vz = ex - sx, ey - sy, ez - sz
    wx, wy, wz = px - sx, py - sy, pz - sz
    length_sq = vx * vx + vy * vy + vz * vz
    if length_sq == 0.0:
        return distance(point, start)
    t = max(0.0, min(1.0, (wx * vx + wy * vy + wz * vz) / length_sq))
    projection = (sx + t * vx, sy + t * vy, sz + t * vz)
    return distance(point, projection)
