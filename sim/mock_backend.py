"""Mock geometry backend that preserves the Stage 1.5 FK/collision behavior."""

from __future__ import annotations

from robot_safety.collision import check_trajectory_collision

from .base import BackendReviewResult


class MockGeometryBackend:
    name = "mock"

    def replay_joint_trajectory(self, *, scene, trajectory: list[tuple[float, ...]]) -> BackendReviewResult:
        result = check_trajectory_collision(trajectory, scene.robot, scene.obstacles)
        return BackendReviewResult(
            backend_name=self.name,
            collision_free=result.collision_free,
            min_clearance=result.min_clearance,
            closest_robot_link=result.closest_robot_link,
            closest_obstacle=result.closest_obstacle,
            worst_step=result.worst_step,
            violations=result.violations,
            metadata={
                "model_version": "mock_geometry_v1",
                "collision_method": "segment_sphere_clearance",
            },
        )
