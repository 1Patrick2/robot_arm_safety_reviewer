from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import json

# ── External trajectory data types ──────────────────────────────────────


@dataclass(frozen=True)
class ExternalActionFrame:
    """A single action frame from an external robot trajectory."""

    step_index: int
    action: tuple[float, ...]
    action_type: str
    source: str
    timestamp: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExternalTrajectory:
    """A complete external robot trajectory (dataset episode)."""

    dataset_name: str
    episode_id: str
    action_type: str
    frames: tuple[ExternalActionFrame, ...]
    robot_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionMappingConfig:
    """Configuration for mapping an external trajectory to a PolicyActionSequence."""

    source_action_type: str = "joint_position"
    target_command_type: str = "joint_space"
    joint_count: int = 6
    speed: float = 0.5
    scale: float = 1.0
    offset: tuple[float, ...] | None = None
    current_joints_policy: str = "previous_target"

    def __post_init__(self) -> None:
        if self.joint_count <= 0:
            raise ValueError(f"joint_count must be > 0, got {self.joint_count}")
        if self.offset is not None and len(self.offset) != self.joint_count:
            raise ValueError(
                f"offset length {len(self.offset)} != joint_count {self.joint_count}"
            )
        if self.current_joints_policy not in {"zeros", "previous_target"}:
            raise ValueError(
                f"current_joints_policy must be 'zeros' or 'previous_target', "
                f"got '{self.current_joints_policy}'"
            )


# ── Conversion ──────────────────────────────────────────────────────────


def external_trajectory_to_policy_sequence(
    trajectory: ExternalTrajectory,
    mapping: ActionMappingConfig,
) -> Any:
    """Convert an ``ExternalTrajectory`` into a ``PolicyActionSequence``.

    Args:
        trajectory: The external trajectory to convert.
        mapping: Mapping configuration for the conversion.

    Returns:
        A ``PolicyActionSequence`` ready for ``SafetyRuntime`` evaluation.

    Raises:
        ValueError: If *source_action_type* is unsupported or any action
            dimension does not match *mapping.joint_count*.
    """
    from robot.runtime.policy_action import PolicyAction  # noqa: PLC0415
    from robot.runtime.action_sequence import PolicyActionSequence  # noqa: PLC0415

    if trajectory.action_type != mapping.source_action_type:
        raise ValueError(
            f"Unsupported source_action_type '{trajectory.action_type}'; "
            f"expected '{mapping.source_action_type}'"
        )

    actions: list[PolicyAction] = []

    for fi, frame in enumerate(trajectory.frames):
        action = list(frame.action)

        if len(action) != mapping.joint_count:
            raise ValueError(
                f"Frame {fi}: action dimension {len(action)} != "
                f"joint_count {mapping.joint_count}"
            )

        # Apply scale / offset
        mapped = [
            (v * mapping.scale) + (mapping.offset[i] if mapping.offset else 0.0)
            for i, v in enumerate(action)
        ]

        actions.append(PolicyAction(
            action_type="joint_target",
            values=tuple(mapped),
            timestamp=frame.timestamp or fi * mapping.speed,
        ))


    seq_id = f"{trajectory.dataset_name}__{trajectory.episode_id}"
    return PolicyActionSequence(
        sequence_id=seq_id,
        source="external_trajectory",
        initial_joints=(0.0,) * mapping.joint_count,
        actions=tuple(actions),
        metadata={
            "dataset_name": trajectory.dataset_name,
            "episode_id": trajectory.episode_id,
            "external_robot": trajectory.robot_name or "",
            "external_action_type": trajectory.action_type,
        },
    )
