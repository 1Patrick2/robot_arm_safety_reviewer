from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from perception.models import PerceptionResult


@dataclass(frozen=True)
class PerceptionInferenceRequest:
    """A request to run perception inference on an input source.

    Attributes:
        input_path: Path to the input (image, mock file, etc.).
        sequence_id: Optional sequence identifier for traceability.
        frame_id: Frame identifier used in the output ``PerceptionResult``.
        metadata: Additional context (e.g. model params, runtime flags).
    """

    input_path: Path
    sequence_id: str | None = None
    frame_id: str = "frame_000001"
    metadata: dict[str, Any] = field(default_factory=dict)


class PerceptionModelAdapter(Protocol):
    """Protocol for a perception model adapter.

    The adapter is the boundary between a model and the robot safety system.
    It must produce ``PerceptionResult`` only — it must not produce safety
    decisions, approve/reject/manual_review, or call ``SafetyRuntime`` or
    ``RobotDeviceAdapter``.
    """

    def infer(self, request: PerceptionInferenceRequest) -> PerceptionResult:
        """Run inference and return a structured perception result."""
        ...
