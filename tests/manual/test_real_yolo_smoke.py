"""Real YOLO smoke test — requires ultralytics, a model file, and an image.

Skipped unless ``RUN_REAL_YOLO_SMOKE`` environment variable is set.
"""

import os
from pathlib import Path

import pytest

REAL_YOLO_MODEL = os.environ.get("REAL_YOLO_MODEL")
REAL_YOLO_IMAGE = os.environ.get("REAL_YOLO_IMAGE")

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_REAL_YOLO_SMOKE"),
    reason="Set RUN_REAL_YOLO_SMOKE=1 with REAL_YOLO_MODEL and REAL_YOLO_IMAGE",
)


def test_model_and_image_exist():
    assert REAL_YOLO_MODEL, "REAL_YOLO_MODEL not set"
    assert REAL_YOLO_IMAGE, "REAL_YOLO_IMAGE not set"
    assert Path(REAL_YOLO_MODEL).exists(), f"Model not found: {REAL_YOLO_MODEL}"
    assert Path(REAL_YOLO_IMAGE).exists(), f"Image not found: {REAL_YOLO_IMAGE}"


def test_adapter_returns_perception_result(tmp_path):
    from perception.adapters.ultralytics_yolo_adapter import UltralyticsYoloAdapter  # noqa: PLC0415
    from perception.adapters.base import PerceptionInferenceRequest  # noqa: PLC0415

    adapter = UltralyticsYoloAdapter(
        REAL_YOLO_MODEL,
        confidence_threshold=0.25,
        default_zone_by_class={"person": "danger_zone"},
    )
    request = PerceptionInferenceRequest(
        input_path=Path(REAL_YOLO_IMAGE),
        sequence_id="real_yolo_smoke",
        frame_id="frame_000001",
    )
    result = adapter.infer(request)
    assert result.schema_version == "perception_result.v1"
    assert len(result.frames) >= 1

    frame = result.frames[0]
    if len(frame.detections) > 0:
        det = frame.detections[0]
        assert det.confidence > 0
        assert det.class_name


def test_full_evidence_chain(tmp_path):
    from perception.adapters.ultralytics_yolo_adapter import UltralyticsYoloAdapter  # noqa: PLC0415
    from perception.adapters.base import PerceptionInferenceRequest  # noqa: PLC0415
    from perception.inference_runner import run_perception_inference  # noqa: PLC0415
    from perception.inference_record import write_perception_inference_record  # noqa: PLC0415
    from diagnostics.evidence.manifest import build_evidence_manifest  # noqa: PLC0415

    adapter = UltralyticsYoloAdapter(
        REAL_YOLO_MODEL,
        confidence_threshold=0.25,
        default_zone_by_class={"person": "danger_zone"},
    )
    request = PerceptionInferenceRequest(
        input_path=Path(REAL_YOLO_IMAGE),
        sequence_id="real_yolo_smoke",
        frame_id="frame_000001",
    )
    record = run_perception_inference(
        adapter=adapter,
        request=request,
        original_decision="approve",
        original_risk_level="low",
    )
    rec_path = tmp_path / "perception_inference_record.json"
    write_perception_inference_record(record, rec_path)

    ctx = tmp_path / "diagnostic_context.json"
    ctx.write_text('{"episode_id": "real_yolo", "artifacts": []}', encoding="utf-8")

    manifest = build_evidence_manifest(context_path=ctx, perception_record_path=rec_path)
    assert manifest["checks"]["has_perception_evidence"] is True
    assert manifest["evidence_groups"]["perception"]["available"] is True
