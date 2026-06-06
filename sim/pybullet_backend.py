"""PyBullet backend for replaying joint trajectories against a URDF arm."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Literal

from robot_safety.models import Violation

from .base import BackendReviewResult, SimulationBackend


LINK_POSITION_METHOD = "link_position_sphere_clearance"
CLOSEST_POINTS_METHOD = "pybullet_closest_points_sphere_collision"
DEFAULT_CLOSEST_POINT_DISTANCE = 0.30
CONTACT_DISTANCE_INDEX = 8

CollisionMethod = Literal[
    "link_position_sphere_clearance",
    "pybullet_closest_points_sphere_collision",
]


class PyBulletBackend(SimulationBackend):
    name = "pybullet"

    def __init__(
        self,
        urdf_path: Path | None = None,
        *,
        collision_method: CollisionMethod = CLOSEST_POINTS_METHOD,
        closest_point_search_distance: float = DEFAULT_CLOSEST_POINT_DISTANCE,
        include_base_collision: bool = False,
    ) -> None:
        if collision_method not in {LINK_POSITION_METHOD, CLOSEST_POINTS_METHOD}:
            raise ValueError(f"unsupported PyBullet collision method: {collision_method}")
        self.urdf_path = urdf_path or (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "robots"
            / "mock_realman_6dof"
            / "robot.urdf"
        )
        self.collision_method = collision_method
        self.closest_point_search_distance = closest_point_search_distance
        self.include_base_collision = include_base_collision

    def replay_joint_trajectory(self, *, scene, trajectory: list[tuple[float, ...]]) -> BackendReviewResult:
        import pybullet

        client_id = pybullet.connect(pybullet.DIRECT)
        try:
            robot_id = pybullet.loadURDF(
                str(self.urdf_path),
                basePosition=scene.robot.base_position,
                baseOrientation=scene.robot.base_orientation,
                physicsClientId=client_id,
            )
            if robot_id < 0:
                raise RuntimeError(f"failed to load URDF: {self.urdf_path}")
            return self._review_loaded_robot(pybullet, client_id, robot_id, scene, trajectory)
        finally:
            pybullet.disconnect(client_id)

    def _review_loaded_robot(self, pybullet, client_id: int, robot_id: int, scene, trajectory) -> BackendReviewResult:
        if not scene.obstacles:
            return BackendReviewResult(
                backend_name=self.name,
                collision_free=True,
                min_clearance=999.0,
                closest_robot_link=None,
                closest_obstacle=None,
                worst_step=None,
                violations=(),
                metadata=self._metadata(checked_links=[]),
            )

        if self.collision_method == LINK_POSITION_METHOD:
            return self._review_by_link_positions(pybullet, client_id, robot_id, scene, trajectory)
        return self._review_by_closest_points(pybullet, client_id, robot_id, scene, trajectory)

    def _review_by_link_positions(self, pybullet, client_id: int, robot_id: int, scene, trajectory) -> BackendReviewResult:
        revolute_joints = self._revolute_joints(pybullet, client_id, robot_id)
        link_radius = scene.robot.link_radius
        min_clearance = math.inf
        closest_robot_link = None
        closest_obstacle = None
        worst_step = None
        worst_violations: tuple[Violation, ...] = ()

        for step, joints in enumerate(trajectory):
            for joint_index, joint_value in zip(revolute_joints, joints):
                pybullet.resetJointState(robot_id, joint_index, joint_value, physicsClientId=client_id)

            step_violations: list[Violation] = []
            for link_name, position in self._link_positions(pybullet, client_id, robot_id):
                for obstacle in scene.obstacles:
                    clearance = math.dist(position, obstacle.position) - obstacle.radius - link_radius
                    if clearance < min_clearance:
                        min_clearance = clearance
                        closest_robot_link = link_name
                        closest_obstacle = obstacle.obstacle_id
                        worst_step = step
                    if clearance < 0:
                        step_violations.append(
                            Violation(
                                type="environment_collision",
                                message=f"{link_name} collides with {obstacle.obstacle_id}.",
                                object=obstacle.obstacle_id,
                                link=link_name,
                                step=step,
                                clearance=round(clearance, 6),
                            )
                        )
            if step == worst_step:
                worst_violations = tuple(step_violations)

        return BackendReviewResult(
            backend_name=self.name,
            collision_free=not worst_violations,
            min_clearance=round(min_clearance, 6),
            closest_robot_link=closest_robot_link,
            closest_obstacle=closest_obstacle,
            worst_step=worst_step,
            violations=worst_violations,
            metadata=self._metadata(),
        )

    def _review_by_closest_points(self, pybullet, client_id: int, robot_id: int, scene, trajectory) -> BackendReviewResult:
        revolute_joints = self._revolute_joints(pybullet, client_id, robot_id)
        link_name_map = self._link_name_map(pybullet, client_id, robot_id)
        checked_links = list(link_name_map.values())
        obstacle_bodies = self._create_sphere_obstacles(pybullet, client_id, scene.obstacles)
        min_clearance = math.inf
        closest_robot_link = None
        closest_obstacle = None
        worst_step = None
        worst_violations: tuple[Violation, ...] = ()

        for step, joints in enumerate(trajectory):
            for joint_index, joint_value in zip(revolute_joints, joints):
                pybullet.resetJointState(robot_id, joint_index, joint_value, physicsClientId=client_id)
            pybullet.performCollisionDetection(physicsClientId=client_id)

            for link_index, link_name in link_name_map.items():
                for obstacle, obstacle_body_id in obstacle_bodies:
                    points = pybullet.getClosestPoints(
                        bodyA=robot_id,
                        bodyB=obstacle_body_id,
                        distance=self.closest_point_search_distance,
                        linkIndexA=link_index,
                        linkIndexB=-1,
                        physicsClientId=client_id,
                    )
                    for point in points:
                        clearance = float(point[CONTACT_DISTANCE_INDEX])
                        if clearance < min_clearance:
                            min_clearance = clearance
                            closest_robot_link = link_name
                            closest_obstacle = obstacle.obstacle_id
                            worst_step = step
                            worst_violations = self._violations_for_clearance(
                                clearance=clearance,
                                link_name=link_name,
                                obstacle_id=obstacle.obstacle_id,
                                step=step,
                            )

        if math.isinf(min_clearance):
            min_clearance = 999.0

        return BackendReviewResult(
            backend_name=self.name,
            collision_free=min_clearance >= 0.0,
            min_clearance=round(min_clearance, 6),
            closest_robot_link=closest_robot_link,
            closest_obstacle=closest_obstacle,
            worst_step=worst_step,
            violations=worst_violations,
            metadata=self._metadata(checked_links=checked_links),
        )

    def _violations_for_clearance(
        self,
        *,
        clearance: float,
        link_name: str,
        obstacle_id: str,
        step: int,
    ) -> tuple[Violation, ...]:
        if clearance >= 0:
            return ()
        return (
            Violation(
                type="environment_collision",
                message=f"{link_name} collides with {obstacle_id}.",
                object=obstacle_id,
                link=link_name,
                step=step,
                clearance=round(clearance, 6),
            ),
        )

    def _metadata(self, *, checked_links: list[str] | None = None) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "mode": "DIRECT",
            "urdf_path": str(self.urdf_path),
            "collision_method": self.collision_method,
        }
        if self.collision_method == CLOSEST_POINTS_METHOD:
            metadata.update(
                {
                    "fidelity": "collision_geometry",
                    "notes": (
                        "Uses PyBullet closest-point queries over URDF collision geometry "
                        "and sphere obstacle bodies."
                    ),
                    "closest_point_search_distance": self.closest_point_search_distance,
                    "include_base_collision": self.include_base_collision,
                    "checked_links": checked_links or [],
                }
            )
        else:
            metadata.update(
                {
                    "fidelity": "approximate",
                    "notes": "Uses link-frame position sampling, not full collision geometry.",
                }
            )
        return metadata

    def _revolute_joints(self, pybullet, client_id: int, robot_id: int) -> list[int]:
        joint_indices = []
        for index in range(pybullet.getNumJoints(robot_id, physicsClientId=client_id)):
            joint_info = pybullet.getJointInfo(robot_id, index, physicsClientId=client_id)
            if joint_info[2] == pybullet.JOINT_REVOLUTE:
                joint_indices.append(index)
        return joint_indices

    def _link_positions(self, pybullet, client_id: int, robot_id: int):
        base_position, _ = pybullet.getBasePositionAndOrientation(robot_id, physicsClientId=client_id)
        yield "base_link", tuple(float(value) for value in base_position)

        for index in range(pybullet.getNumJoints(robot_id, physicsClientId=client_id)):
            joint_info = pybullet.getJointInfo(robot_id, index, physicsClientId=client_id)
            link_name = joint_info[12].decode("utf-8")
            link_state = pybullet.getLinkState(robot_id, index, physicsClientId=client_id)
            yield link_name, tuple(float(value) for value in link_state[0])

    def _link_name_map(self, pybullet, client_id: int, robot_id: int) -> dict[int, str]:
        link_names: dict[int, str] = {}
        if self.include_base_collision:
            link_names[-1] = "base_link"
        for index in range(pybullet.getNumJoints(robot_id, physicsClientId=client_id)):
            joint_info = pybullet.getJointInfo(robot_id, index, physicsClientId=client_id)
            link_names[index] = joint_info[12].decode("utf-8")
        return link_names

    def _create_sphere_obstacles(self, pybullet, client_id: int, obstacles):
        obstacle_bodies = []
        for obstacle in obstacles:
            collision_shape = pybullet.createCollisionShape(
                pybullet.GEOM_SPHERE,
                radius=obstacle.radius,
                physicsClientId=client_id,
            )
            body_id = pybullet.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=collision_shape,
                basePosition=obstacle.position,
                physicsClientId=client_id,
            )
            obstacle_bodies.append((obstacle, body_id))
        return obstacle_bodies
