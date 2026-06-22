from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import PerceptionDetection, PerceptionFrame, PerceptionResult


def load_perception_result(path: str | Path) -> PerceptionResult:
    """Load and validate a ``perception_result.v1`` JSON file.

    Args:
        path: Path to the perception result JSON file.

    Returns:
        A validated ``PerceptionResult`` instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If validation fails.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"perception result not found: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in perception result: {path}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"perception result must be a JSON object, got {type(raw).__name__}")

    # schema_version
    sv = raw.get("schema_version")
    if sv != "perception_result.v1":
        raise ValueError(
            f"unsupported schema_version '{sv}'; expected 'perception_result.v1'"
        )

    # frames
    frames_raw = raw.get("frames")
    if not isinstance(frames_raw, list):
        raise ValueError("'frames' must be a list")

    frames: list[PerceptionFrame] = []
    for fi, frame_raw in enumerate(frames_raw):
        if not isinstance(frame_raw, dict):
            raise ValueError(f"frames[{fi}] must be a JSON object")

        frame_id = frame_raw.get("frame_id")
        if not frame_id or not isinstance(frame_id, str):
            raise ValueError(f"frames[{fi}] missing valid 'frame_id' string")

        dets_raw = frame_raw.get("detections")
        if not isinstance(dets_raw, list):
            raise ValueError(f"frames[{fi}].detections must be a list")

        detections: list[PerceptionDetection] = []
        for di, det_raw in enumerate(dets_raw):
            if not isinstance(det_raw, dict):
                raise ValueError(f"frames[{fi}].detections[{di}] must be a JSON object")

            object_id = det_raw.get("object_id")
            if not object_id or not isinstance(object_id, str):
                raise ValueError(
                    f"frames[{fi}].detections[{di}] missing valid 'object_id' string"
                )

            class_name = det_raw.get("class_name")
            if not class_name or not isinstance(class_name, str):
                raise ValueError(
                    f"frames[{fi}].detections[{di}] missing valid 'class_name' string"
                )

            confidence = det_raw.get("confidence")
            if not isinstance(confidence, (int, float)):
                raise ValueError(
                    f"frames[{fi}].detections[{di}].confidence must be a number"
                )
            confidence = float(confidence)
            if not (0.0 <= confidence <= 1.0):
                raise ValueError(
                    f"frames[{fi}].detections[{di}].confidence must be in [0.0, 1.0], got {confidence}"
                )

            bbox_raw = det_raw.get("bbox_xyxy")
            bbox: tuple[float, float, float, float] | None = None
            if bbox_raw is not None:
                if not isinstance(bbox_raw, (list, tuple)) or len(bbox_raw) != 4:
                    raise ValueError(
                        f"frames[{fi}].detections[{di}].bbox_xyxy must be a list of 4 numbers"
                    )
                bbox = tuple(float(v) for v in bbox_raw)  # type: ignore[arg-type]

            zone = det_raw.get("zone")
            if zone is not None and not isinstance(zone, str):
                raise ValueError(
                    f"frames[{fi}].detections[{di}].zone must be a string or null"
                )

            distance = det_raw.get("distance_m")
            if distance is not None:
                if not isinstance(distance, (int, float)):
                    raise ValueError(
                        f"frames[{fi}].detections[{di}].distance_m must be a number or null"
                    )
                distance = float(distance)
                if distance < 0:
                    raise ValueError(
                        f"frames[{fi}].detections[{di}].distance_m must be >= 0, got {distance}"
                    )

            detections.append(PerceptionDetection(
                object_id=object_id,
                class_name=class_name,
                confidence=confidence,
                bbox_xyxy=bbox,
                zone=zone,
                distance_m=distance,
            ))

        frames.append(PerceptionFrame(
            frame_id=frame_id,
            timestamp=frame_raw.get("timestamp"),
            detections=tuple(detections),
        ))

    return PerceptionResult(
        schema_version=sv,
        sequence_id=raw.get("sequence_id"),
        frames=tuple(frames),
    )
