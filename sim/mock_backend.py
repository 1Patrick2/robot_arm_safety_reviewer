"""Mock geometry backend that preserves the Stage 1.5 FK/collision behavior."""

from __future__ import annotations

from robot_safety.collision import check_trajectory_collision

from .base import BackendReviewResult

'''这个 mock backend 的作用是复现 Stage 1.5 的碰撞检查行为，主要用来做基准测试和对比。它直接调用我们之前实现的纯几何碰撞检查函数 check_trajectory_collision，来计算轨迹的碰撞结果，并把结果封装成 BackendReviewResult 返回。这样我们就可以在不依赖物理引擎的情况下，验证我们的碰撞检查逻辑是否正确，以及后续 PyBullet 后端的实现是否与之保持一致。'''
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
