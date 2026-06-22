from pathlib import Path

from perception.models import PerceptionDetection, PerceptionResult
from perception.adapters.base import PerceptionInferenceRequest
from perception.adapters.fake_model_adapter import FakePerceptionModelAdapter
from perception.fake_adapter import build_safety_observations
from perception.fusion import fuse_safety_with_perception


class TestFakePerceptionModelAdapter:
    def test_adapter_returns_valid_perception_result(self):
        adapter = FakePerceptionModelAdapter(
            detections=(
                PerceptionDetection(
                    object_id="person_1",
                    class_name="person",
                    confidence=0.9,
                ),
            ),
        )
        result = adapter.infer(PerceptionInferenceRequest(input_path=Path("mock")))
        assert result.schema_version == "perception_result.v1"
        assert len(result.frames) == 1
        assert len(result.frames[0].detections) == 1

    def test_sequence_id_and_frame_id_are_propagated(self):
        adapter = FakePerceptionModelAdapter(
            detections=(
                PerceptionDetection(
                    object_id="person_1",
                    class_name="person",
                    confidence=0.9,
                    zone="warning_zone",
                ),
            ),
        )
        result = adapter.infer(PerceptionInferenceRequest(
            input_path=Path("mock"),
            sequence_id="case_001",
            frame_id="frame_000123",
        ))
        assert result.sequence_id == "case_001"
        assert result.frames[0].frame_id == "frame_000123"

    def test_output_can_enter_build_safety_observations(self):
        adapter = FakePerceptionModelAdapter(
            detections=(
                PerceptionDetection(
                    object_id="person_1",
                    class_name="person",
                    confidence=0.9,
                    zone="danger_zone",
                ),
            ),
        )
        result = adapter.infer(PerceptionInferenceRequest(input_path=Path("mock")))
        observations = build_safety_observations(result)
        kinds = {o.kind for o in observations}
        assert "human_in_danger_zone" in kinds

    def test_output_can_enter_fuse_safety_with_perception(self):
        adapter = FakePerceptionModelAdapter(
            detections=(
                PerceptionDetection(
                    object_id="person_1",
                    class_name="person",
                    confidence=0.9,
                    zone="danger_zone",
                ),
            ),
        )
        result = adapter.infer(PerceptionInferenceRequest(input_path=Path("mock")))
        observations = build_safety_observations(result)
        fused = fuse_safety_with_perception(
            original_decision="approve",
            original_risk_level="low",
            observations=observations,
        )
        assert fused.fused_decision == "reject"
        assert fused.fused_risk_level == "high"

    def test_adapter_does_not_expose_safety_api(self):
        adapter = FakePerceptionModelAdapter()
        forbidden = {"approve", "reject", "manual_review", "send_action", "execute", "step"}
        adapter_methods = {m for m in dir(adapter) if not m.startswith("_")}
        assert not (forbidden & adapter_methods), (
            f"Adapter exposes forbidden safety methods: {forbidden & adapter_methods}"
        )

    def test_no_real_model_dependency(self):
        """Verify the test environment does not force real model imports."""
        import sys
        forbidden_modules = {"onnxruntime", "torch", "cv2", "rknn"}
        loaded = {m.split(".")[0] for m in sys.modules}
        assert not (forbidden_modules & loaded), (
            f"Forbidden model modules are loaded: {forbidden_modules & loaded}"
        )

    def test_preset_result_overrides_detections(self):
        """When both result and detections are given, result takes precedence."""
        preset_result = PerceptionResult(
            schema_version="perception_result.v1",
            sequence_id="preset_seq",
        )
        adapter = FakePerceptionModelAdapter(
            detections=(
                PerceptionDetection(
                    object_id="person_1",
                    class_name="person",
                    confidence=0.9,
                ),
            ),
            result=preset_result,
        )
        result = adapter.infer(PerceptionInferenceRequest(
            input_path=Path("mock"),
            sequence_id="request_seq",
        ))
        # Preset result takes precedence; sequence_id from request overrides
        assert result.sequence_id == "request_seq"
        assert len(result.frames) == 0  # preset result has no frames

    def test_preset_result_is_not_mutated_by_infer(self):
        """The original preset_result must remain unchanged after infer()."""
        preset_result = PerceptionResult(
            schema_version="perception_result.v1",
            sequence_id="preset_seq",
        )
        adapter = FakePerceptionModelAdapter(result=preset_result)
        result = adapter.infer(PerceptionInferenceRequest(
            input_path=Path("mock"),
            sequence_id="request_seq",
        ))
        assert result.sequence_id == "request_seq"
        # Original must not be mutated
        assert preset_result.sequence_id == "preset_seq"
