"""Capability test: perception pipeline — schema, adapter, fusion, evidence."""

import json
from pathlib import Path
import ast
import pytest


def test_perception_result_schema_validation(tmp_path):
    from perception.loader import load_perception_result
    p = tmp_path / "valid.json"
    p.write_text(json.dumps({
        "schema_version": "perception_result.v1",
        "frames": [{"frame_id": "f1", "detections": [{"object_id": "o1", "class_name": "person", "confidence": 0.9}]}]
    }), encoding="utf-8")
    result = load_perception_result(p)
    assert result.schema_version == "perception_result.v1"
    assert len(result.frames) == 1


def test_perception_invalid_schema_raises(tmp_path):
    from perception.loader import load_perception_result
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"schema_version": "perception_result.v0"}), encoding="utf-8")
    import pytest
    with pytest.raises(ValueError, match="schema_version"):
        load_perception_result(p)


def test_fake_adapter_returns_perception_result():
    from perception.adapters.fake_model_adapter import FakePerceptionModelAdapter
    from perception.adapters.base import PerceptionInferenceRequest
    from perception.models import PerceptionDetection
    from pathlib import Path
    adapter = FakePerceptionModelAdapter(detections=(
        PerceptionDetection(object_id="p1", class_name="person", confidence=0.9, zone="danger_zone"),
    ))
    result = adapter.infer(PerceptionInferenceRequest(input_path=Path("mock")))
    assert result.schema_version == "perception_result.v1"
    assert len(result.frames[0].detections) == 1


def test_perception_fusion_escalates_human_danger_to_reject():
    from perception.models import PerceptionDetection, PerceptionResult, PerceptionFrame
    from perception.fake_adapter import build_safety_observations
    from perception.fusion import fuse_safety_with_perception
    result = PerceptionResult(frames=(
        PerceptionFrame(frame_id="f1", detections=(
            PerceptionDetection(object_id="p1", class_name="person", confidence=0.9, zone="danger_zone"),
        )),
    ))
    obs = build_safety_observations(result)
    fused = fuse_safety_with_perception(original_decision="approve", observations=obs)
    assert fused.fused_decision == "reject"
    assert fused.fused_risk_level == "high"


def test_perception_inference_evidence(tmp_path):
    from perception.adapters.fake_model_adapter import FakePerceptionModelAdapter
    from perception.adapters.base import PerceptionInferenceRequest
    from perception.inference_runner import run_perception_inference
    from perception.inference_record import write_perception_inference_record
    from pathlib import Path
    adapter = FakePerceptionModelAdapter(detections=())
    request = PerceptionInferenceRequest(input_path=Path(__file__), frame_id="f1")
    record = run_perception_inference(adapter=adapter, request=request, original_decision="approve")
    out = tmp_path / "record.json"
    write_perception_inference_record(record, out)
    assert out.exists()


def test_ultralytics_adapter_contract():
    """No ultralytics at top level, no safety methods exposed."""
    import ast, inspect
    from perception.adapters.ultralytics_yolo_adapter import UltralyticsYoloAdapter
    source = inspect.getsource(UltralyticsYoloAdapter)
    # Check only top-level (module-level) imports — NOT function-body lazy imports
    tree = ast.parse(source)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.split(".")[0] for a in node.names] + ([node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
            if "ultralytics" in names:
                pytest.fail(f"ultralytics imported at module level")
    forbidden = {"approve", "reject", "manual_review", "send_action", "execute", "step"}
    adapter_methods = {m for m in dir(UltralyticsYoloAdapter("dummy.pt")) if not m.startswith("_")}
    assert not (forbidden & adapter_methods)
