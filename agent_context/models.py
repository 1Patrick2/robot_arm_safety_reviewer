from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Default limitations injected into every AgentContext.
# These are deterministic safety boundary statements — not LLM output.
# ---------------------------------------------------------------------------
DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "This project is a deterministic safety reviewer, not a planner.",
    "Safety decisions come from deterministic safety runtime, not from an LLM.",
    "The diagnostic agent must not approve, reject, modify, or execute robot actions.",
    "PyBullet backend is a diagnostic simulation backend, not certified hardware validation.",
)


def _immutable_copy(value: Any) -> Any:
    """Recursively convert lists to tuples for hashability."""
    if isinstance(value, list):
        return tuple(_immutable_copy(v) for v in value)
    if isinstance(value, dict):
        return {k: _immutable_copy(v) for k, v in value.items()}
    return value


@dataclass(frozen=True)
class AgentContextArtifact:
    """A file artifact referenced in a diagnostic context."""

    kind: str
    path: str
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "path": self.path,
            "description": self.description,
        }


@dataclass(frozen=True)
class AgentContextStep:
    """A single step selected for diagnostic context."""

    step_index: int | None = None
    step_id: str | None = None
    decision: str | None = None
    risk_level: str | None = None
    executed: bool = False
    blocked_reason: str | None = None
    min_clearance: float | None = None
    closest_robot_link: str | None = None
    closest_obstacle: str | None = None
    backend_worst_step: int | None = None
    proposed_action: dict[str, Any] = field(default_factory=dict)
    safety_result: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Normalize mutable defaults to immutable
        object.__setattr__(self, "proposed_action", dict(self.proposed_action))
        object.__setattr__(self, "safety_result", dict(self.safety_result))

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "step_id": self.step_id,
            "decision": self.decision,
            "risk_level": self.risk_level,
            "executed": self.executed,
            "blocked_reason": self.blocked_reason,
            "min_clearance": self.min_clearance,
            "closest_robot_link": self.closest_robot_link,
            "closest_obstacle": self.closest_obstacle,
            "backend_worst_step": self.backend_worst_step,
            "proposed_action": dict(self.proposed_action),
            "safety_result": dict(self.safety_result),
        }


@dataclass(frozen=True)
class AgentContext:
    """Deterministic diagnostic context package for a single episode."""

    episode_id: str
    sequence_id: str | None = None
    backend: str | None = None
    device: str | None = None
    run_mode: str | None = None
    total_steps: int = 0
    approved_steps: int = 0
    executed_steps: int = 0
    blocked_steps: int = 0
    rejected_steps: int = 0
    manual_review_steps: int = 0
    min_clearance: float | None = None
    worst_sequence_step_index: int | None = None
    backend_worst_step: int | None = None
    closest_robot_link: str | None = None
    closest_obstacle: str | None = None
    critical_steps: tuple[AgentContextStep, ...] = field(default_factory=tuple)
    artifacts: tuple[AgentContextArtifact, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=lambda: DEFAULT_LIMITATIONS)

    def __post_init__(self) -> None:
        # Normalise list inputs to tuples for immutability
        if isinstance(self.critical_steps, list):
            object.__setattr__(self, "critical_steps", tuple(self.critical_steps))
        if isinstance(self.artifacts, list):
            object.__setattr__(self, "artifacts", tuple(self.artifacts))
        if isinstance(self.limitations, list):
            object.__setattr__(self, "limitations", tuple(self.limitations))

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "sequence_id": self.sequence_id,
            "backend": self.backend,
            "device": self.device,
            "run_mode": self.run_mode,
            "total_steps": self.total_steps,
            "approved_steps": self.approved_steps,
            "executed_steps": self.executed_steps,
            "blocked_steps": self.blocked_steps,
            "rejected_steps": self.rejected_steps,
            "manual_review_steps": self.manual_review_steps,
            "min_clearance": self.min_clearance,
            "worst_sequence_step_index": self.worst_sequence_step_index,
            "backend_worst_step": self.backend_worst_step,
            "closest_robot_link": self.closest_robot_link,
            "closest_obstacle": self.closest_obstacle,
            "critical_steps": [s.to_dict() for s in self.critical_steps],
            "artifacts": [a.to_dict() for a in self.artifacts],
            "limitations": list(self.limitations),
        }
