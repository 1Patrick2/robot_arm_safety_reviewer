from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PerceptionDetection:
    """A single detected object in a perception frame.

    Attributes:
        object_id: Unique identifier for the detected object (e.g. ``"person_1"``).
        class_name: Object class, e.g. ``"person"``, ``"hand"``, ``"obstacle"``, ``"unknown"``.
        confidence: Detection confidence in ``[0.0, 1.0]``.
        bbox_xyxy: Optional 2D bounding box ``(x1, y1, x2, y2)`` in image coordinates.
        zone: Optional safety zone classification, e.g. ``"safe_zone"``, ``"warning_zone"``, ``"danger_zone"``.
        distance_m: Optional estimated distance from the robot in metres.
    """

    object_id: str
    class_name: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float] | None = None
    zone: str | None = None
    distance_m: float | None = None


@dataclass(frozen=True)
class PerceptionFrame:
    """A single frame of perception results.

    Attributes:
        frame_id: Frame identifier (e.g. ``"frame_0001"``).
        timestamp: Optional ISO-8601 timestamp string.
        detections: Detected objects in this frame.
    """

    frame_id: str
    timestamp: str | None = None
    detections: tuple[PerceptionDetection, ...] = ()


@dataclass(frozen=True)
class PerceptionResult:
    """A complete perception result for a sequence or episode.

    Attributes:
        schema_version: Always ``"perception_result.v1"``.
        sequence_id: Optional sequence identifier.
        frames: Per-frame perception data.
    """

    schema_version: str = "perception_result.v1"
    sequence_id: str | None = None
    frames: tuple[PerceptionFrame, ...] = ()


@dataclass(frozen=True)
class SafetyObservation:
    """A structured observation derived from perception results.

    This is not a safety decision — it is a signal from the perception layer
    that may influence downstream safety fusion.

    Attributes:
        kind: Observation type (e.g. ``"human_in_warning_zone"``).
        object_id: The detected object that triggered this observation.
        severity: ``"low"``, ``"medium"``, or ``"high"``.
        frame_id: The frame in which this observation was made.
        evidence_refs: Dot-path references to the perception data fields
            that support this observation.
        metadata: Additional structured context.
    """

    kind: str
    object_id: str | None = None
    severity: str = "low"
    frame_id: str | None = None
    evidence_refs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
