from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from robot_runtime.types import RobotAction, RobotObservation


SUPPORTED_POLICY_ACTION_TYPES = frozenset({"joint_target", "delta_joint"})


def normalize_joint_values(values, field_name: str) -> tuple[float, ...]:
    try:
        result = tuple(float(item) for item in values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of numbers") from exc
    if len(result) != 6:
        raise ValueError(f"{field_name} must contain six values")
    return result


@dataclass(frozen=True)
class PolicyAction:
    action_type: str
    values: tuple[float, ...]
    timestamp: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", normalize_joint_values(self.values, "values"))
        if self.timestamp is not None:
            object.__setattr__(self, "timestamp", float(self.timestamp))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PolicyAction":
        return cls(
            action_type=payload["action_type"],
            values=payload["values"],
            timestamp=payload.get("timestamp"),
            metadata=dict(payload.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "values": list(self.values),
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


def policy_action_to_robot_action(
    observation: RobotObservation,
    action: PolicyAction,
    *,
    speed: float = 0.1,
) -> RobotAction:
    if action.action_type not in SUPPORTED_POLICY_ACTION_TYPES:
        raise ValueError(f"Unsupported policy action type: {action.action_type}")

    if action.action_type == "joint_target":
        target_joints = action.values
    else:
        target_joints = tuple(
            current + delta
            for current, delta in zip(observation.joint_positions, action.values, strict=True)
        )

    metadata = dict(action.metadata)
    metadata["policy_action_type"] = action.action_type
    if action.timestamp is not None:
        metadata["policy_timestamp"] = action.timestamp

    return RobotAction(
        action_type="joint_move",
        target_joints=target_joints,
        speed=speed,
        source="policy_action",
        metadata=metadata,
    )
