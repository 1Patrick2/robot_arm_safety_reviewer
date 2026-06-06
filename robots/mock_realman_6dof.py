"""Mock RealMan-compatible 6-DOF robot adapter."""

from __future__ import annotations

from .base import RobotExecutionResult


class MockRealMan6DoFAdapter:
    """In-memory mock adapter used when no physical RealMan arm is available."""

    def __init__(
        self,
        *,
        robot_id: str = "mock_realman_6dof",
        initial_joints: tuple[float, ...] | list[float] | None = None,
    ) -> None:
        self.robot_id = robot_id
        self._joints = tuple(float(item) for item in (initial_joints or (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)))
        if len(self._joints) != 6:
            raise ValueError("MockRealMan6DoFAdapter requires six initial joints")
        self._stopped = False
        self._last_target_joints: tuple[float, ...] | None = None
        self._execution_count = 0

    def get_joint_state(self) -> tuple[float, ...]:
        return self._joints

    def execute_joint_move(self, target_joints: tuple[float, ...] | list[float], speed: float) -> RobotExecutionResult:
        target = tuple(float(item) for item in target_joints)
        if len(target) != 6:
            raise ValueError("target_joints must contain six values")
        if speed <= 0.0:
            raise ValueError("speed must be positive")
        start = self._joints
        self._joints = target
        self._last_target_joints = target
        self._execution_count += 1
        self._stopped = False
        return RobotExecutionResult(
            robot_id=self.robot_id,
            executed=True,
            success=True,
            reason="mock_execution_complete",
            start_joints=start,
            target_joints=target,
            final_joints=self._joints,
            speed=float(speed),
            simulated=True,
            execution_count=self._execution_count,
        )

    def stop(self) -> None:
        self._stopped = True

    @property
    def stopped(self) -> bool:
        return self._stopped

    @property
    def last_target_joints(self) -> tuple[float, ...] | None:
        return self._last_target_joints

    @property
    def execution_count(self) -> int:
        return self._execution_count
