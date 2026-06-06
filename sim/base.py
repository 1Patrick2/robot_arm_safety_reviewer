"""Common simulation backend interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from robot_safety.models import Violation


@dataclass(frozen=True)
class BackendReviewResult:
    backend_name: str
    collision_free: bool
    min_clearance: float
    closest_robot_link: str | None
    closest_obstacle: str | None
    worst_step: int | None
    violations: tuple[Violation, ...]
    metadata: dict[str, Any]


class SimulationBackend(Protocol):
    name: str

    def replay_joint_trajectory(self, *, scene, trajectory: list[tuple[float, ...]]) -> BackendReviewResult:
        """Replay a joint trajectory and return collision/clearance evidence."""
