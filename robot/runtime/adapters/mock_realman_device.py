from __future__ import annotations

from datetime import datetime, timezone

from robots.mock_realman_6dof import MockRealMan6DoFAdapter

from ..types import RobotAction, RobotObservation, RuntimeExecutionResult


class MockRealManDevice:
    name = "mock_realman_device"

    def __init__(
        self,
        *,
        robot_id: str = "mock_realman_6dof",
        initial_joints: tuple[float, ...] | list[float] | None = None,
    ) -> None:
        self._adapter = MockRealMan6DoFAdapter(robot_id=robot_id, initial_joints=initial_joints)
        self._connected = False

    @property
    def observation_features(self) -> dict:
        return {"joint_positions": (6,)}

    @property
    def action_features(self) -> dict:
        return {"target_joints": (6,), "speed": float}

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def robot_id(self) -> str:
        return self._adapter.robot_id

    @property
    def execution_count(self) -> int:
        return self._adapter.execution_count

    def connect(self, calibrate: bool = True) -> None:
        self._connected = True

    def get_observation(self) -> RobotObservation:
        self._require_connected()
        return RobotObservation(
            robot_id=self.robot_id,
            joint_positions=self._adapter.get_joint_state(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"device": self.name},
        )

    def send_action(self, action: RobotAction) -> RuntimeExecutionResult:
        self._require_connected()
        result = self._adapter.execute_joint_move(action.target_joints, action.speed)
        return RuntimeExecutionResult(
            attempted=result.executed,
            success=result.success,
            reason="executed" if result.success else result.reason,
            simulated=result.simulated,
            metadata=result.to_dict(),
        )

    def disconnect(self) -> None:
        self._connected = False

    def _require_connected(self) -> None:
        if not self._connected:
            raise ConnectionError(f"{self.name} is not connected")
