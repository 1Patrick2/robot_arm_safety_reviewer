from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from robot.safety.models import SafetyResult


def _float_tuple(values, field_name: str) -> tuple[float, ...]:
    try:
        result = tuple(float(item) for item in values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of numbers") from exc
    if len(result) != 6:
        raise ValueError(f"{field_name} must contain six values")
    return result


@dataclass(frozen=True)
class RobotObservation:
    robot_id: str
    joint_positions: tuple[float, ...]
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "joint_positions", _float_tuple(self.joint_positions, "joint_positions"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "robot_id": self.robot_id,
            "joint_positions": list(self.joint_positions),
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RobotAction:
    action_type: str
    target_joints: tuple[float, ...]
    speed: float = 0.1
    source: str = "replay"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action_type != "joint_move":
            raise ValueError("Stage 3 MVP only supports joint_move actions")
        if self.speed <= 0.0:
            raise ValueError("speed must be positive")
        object.__setattr__(self, "target_joints", _float_tuple(self.target_joints, "target_joints"))
        object.__setattr__(self, "speed", float(self.speed))

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "target_joints": list(self.target_joints),
            "speed": self.speed,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeExecutionResult:
    attempted: bool
    success: bool
    reason: str
    simulated: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempted": self.attempted,
            "success": self.success,
            "reason": self.reason,
            "simulated": self.simulated,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeStepResult:
    step_id: str
    observation: RobotObservation
    proposed_action: RobotAction
    safety_result: SafetyResult
    backend_metadata: dict[str, Any]
    executed: bool
    sent_action: RobotAction | None
    execution_result: RuntimeExecutionResult | None
    blocked_reason: str | None
    episode_id: str | None = None
    step_index: int | None = None
    episode_step_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "step_index": self.step_index,
            "step_id": self.step_id,
            "observation": self.observation.to_dict(),
            "proposed_action": self.proposed_action.to_dict(),
            "safety_result": self.safety_result.to_dict(),
            "backend_metadata": dict(self.backend_metadata),
            "executed": self.executed,
            "sent_action": self.sent_action.to_dict() if self.sent_action else None,
            "execution_result": self.execution_result.to_dict() if self.execution_result else None,
            "blocked_reason": self.blocked_reason,
            "episode_step_path": str(self.episode_step_path) if self.episode_step_path else None,
        }
