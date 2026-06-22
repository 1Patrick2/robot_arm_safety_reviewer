from __future__ import annotations

from typing import Any

from .models import PerceptionDetection, PerceptionFrame, PerceptionResult, SafetyObservation

_HUMAN_CLASSES = frozenset({"person", "hand"})


def build_safety_observations(
    perception: PerceptionResult,
    *,
    low_confidence_threshold: float = 0.5,
    close_distance_threshold_m: float = 0.5,
) -> tuple[SafetyObservation, ...]:
    """Convert a ``PerceptionResult`` into structured ``SafetyObservation`` tuples.

    Each detection is evaluated against zone, confidence, and distance rules.
    All observations include ``evidence_refs`` tracing back to the perception data.

    Args:
        perception: A validated ``PerceptionResult``.
        low_confidence_threshold: Detections below this confidence produce
            ``low_confidence_detection`` observations (default 0.5).
        close_distance_threshold_m: Detections at or below this distance
            produce ``close_object_detected`` observations (default 0.5).

    Returns:
        A tuple of ``SafetyObservation`` instances.
    """
    observations: list[SafetyObservation] = []

    for fi, frame in enumerate(perception.frames):
        frame_id = frame.frame_id
        for di, det in enumerate(frame.detections):
            det_refs = _detection_refs(fi, di)

            # --- zone rules ---
            if det.zone is not None and det.class_name in _HUMAN_CLASSES:
                if det.zone == "warning_zone":
                    observations.append(_obs(
                        kind="human_in_warning_zone",
                        object_id=det.object_id,
                        severity="medium",
                        frame_id=frame_id,
                        evidence_refs=(*det_refs, f"perception.frames[{fi}].detections[{di}].zone"),
                    ))
                elif det.zone == "danger_zone":
                    observations.append(_obs(
                        kind="human_in_danger_zone",
                        object_id=det.object_id,
                        severity="high",
                        frame_id=frame_id,
                        evidence_refs=(*det_refs, f"perception.frames[{fi}].detections[{di}].zone"),
                    ))

            if det.zone is not None and det.class_name not in _HUMAN_CLASSES and det.class_name != "unknown":
                if det.zone == "warning_zone":
                    observations.append(_obs(
                        kind="object_in_warning_zone",
                        object_id=det.object_id,
                        severity="medium",
                        frame_id=frame_id,
                        evidence_refs=(*det_refs, f"perception.frames[{fi}].detections[{di}].zone"),
                    ))
                elif det.zone == "danger_zone":
                    observations.append(_obs(
                        kind="object_in_danger_zone",
                        object_id=det.object_id,
                        severity="high",
                        frame_id=frame_id,
                        evidence_refs=(*det_refs, f"perception.frames[{fi}].detections[{di}].zone"),
                    ))

            if det.zone is not None and det.class_name == "unknown":
                severity = "high" if det.zone == "danger_zone" else "medium"
                observations.append(_obs(
                    kind="unknown_object_detected",
                    object_id=det.object_id,
                    severity=severity,
                    frame_id=frame_id,
                    evidence_refs=(*det_refs, f"perception.frames[{fi}].detections[{di}].zone"),
                ))

            # --- confidence rule ---
            if det.confidence < low_confidence_threshold:
                observations.append(_obs(
                    kind="low_confidence_detection",
                    object_id=det.object_id,
                    severity="low",
                    frame_id=frame_id,
                    evidence_refs=det_refs,
                    metadata={"confidence": det.confidence},
                ))

            # --- distance rule ---
            if det.distance_m is not None and det.distance_m < close_distance_threshold_m:
                if det.distance_m < 0.3:
                    dist_severity = "high"
                else:
                    dist_severity = "medium"
                observations.append(_obs(
                    kind="close_object_detected",
                    object_id=det.object_id,
                    severity=dist_severity,
                    frame_id=frame_id,
                    evidence_refs=(*det_refs, f"perception.frames[{fi}].detections[{di}].distance_m"),
                    metadata={"distance_m": det.distance_m},
                ))

    return tuple(observations)


def _detection_refs(fi: int, di: int) -> tuple[str, ...]:
    """Build basic evidence_refs for a detection."""
    prefix = f"perception.frames[{fi}].detections[{di}]"
    return (
        f"{prefix}.class_name",
        f"{prefix}.confidence",
    )


def _obs(
    kind: str,
    object_id: str | None,
    severity: str,
    frame_id: str | None,
    evidence_refs: tuple[str, ...],
    metadata: dict[str, Any] | None = None,
) -> SafetyObservation:
    return SafetyObservation(
        kind=kind,
        object_id=object_id,
        severity=severity,
        frame_id=frame_id,
        evidence_refs=evidence_refs,
        metadata=metadata or {},
    )
