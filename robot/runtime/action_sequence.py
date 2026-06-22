from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .policy_action import PolicyAction, normalize_joint_values


@dataclass(frozen=True)
class PolicyActionSequence:
    sequence_id: str
    initial_joints: tuple[float, ...]
    actions: tuple[PolicyAction, ...]
    source: str
    language_instruction: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial_joints", normalize_joint_values(self.initial_joints, "initial_joints"))
        actions = tuple(
            action if isinstance(action, PolicyAction) else PolicyAction.from_dict(action)
            for action in self.actions
        )
        if not actions:
            raise ValueError("actions must contain at least one action")
        object.__setattr__(self, "actions", actions)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PolicyActionSequence":
        return cls(
            sequence_id=payload["sequence_id"],
            source=payload["source"],
            initial_joints=payload["initial_joints"],
            language_instruction=payload.get("language_instruction"),
            metadata=dict(payload.get("metadata", {})),
            actions=tuple(PolicyAction.from_dict(item) for item in payload["actions"]),
        )

    @classmethod
    def from_json(cls, path: Path) -> "PolicyActionSequence":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence_id": self.sequence_id,
            "source": self.source,
            "initial_joints": list(self.initial_joints),
            "language_instruction": self.language_instruction,
            "metadata": dict(self.metadata),
            "actions": [action.to_dict() for action in self.actions],
        }
