"""Robot adapter interface for future hardware integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RobotExecutionResult:
    robot_id: str
    executed: bool
    success: bool
    reason: str
    start_joints: tuple[float, ...]
    target_joints: tuple[float, ...]
    final_joints: tuple[float, ...]
    speed: float
    simulated: bool = True
    execution_count: int | None = None
    error_code: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict:
        data = {
            "robot_id": self.robot_id,
            "executed": self.executed,
            "success": self.success,
            "reason": self.reason,
            "start_joints": list(self.start_joints),
            "target_joints": list(self.target_joints),
            "final_joints": list(self.final_joints),
            "speed": self.speed,
            "simulated": self.simulated,
            "execution_count": self.execution_count,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }
        return {key: value for key, value in data.items() if value is not None}


class RobotAdapter(Protocol):
    """Minimal robot adapter protocol used by the Stage 1 safety gate."""

    robot_id: str

    def get_joint_state(self) -> tuple[float, ...]:
        """Return current robot joint state."""

    def execute_joint_move(self, target_joints: tuple[float, ...], speed: float) -> RobotExecutionResult:
        """Execute or simulate a joint-space move."""

    def stop(self) -> None:
        """Stop robot motion."""
