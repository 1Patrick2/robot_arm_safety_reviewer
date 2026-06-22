import json
from pathlib import Path

from perception.models import PerceptionDetection, PerceptionResult
from perception.adapters.base import PerceptionInferenceRequest
from perception.adapters.fake_model_adapter import FakePerceptionModelAdapter
from perception.inference_record import (
    PerceptionInferenceRecord,
    write_perception_inference_record,
)
from perception.inference_runner import run_perception_inference
from diagnostics.evidence.manifest import build_evidence_manifest
from diagnostics.contracts.expected import validate_expected_contract


class TestPerceptionInferenceEvidence:
    def test_run_perception_inference_returns_record(self):
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
        request = PerceptionInferenceRequest(
            input_path=Path(__file__),
            sequence_id="test_seq",
            frame_id="f1",
        )
        record = run_perception_inference(
            adapter=adapter,
            request=request,
            original_decision="approve",
            original_risk_level="low",
        )
        assert record.adapter_name == "FakePerceptionModelAdapter"
        assert record.adapter_kind == "fake"
        assert record.input_path == str(Path(__file__))
        assert record.input_exists is True
        assert record.sequence_id == "test_seq"
        assert record.frame_id == "f1"
        assert record.latency_ms >= 0

    def test_human_danger_zone_escalates_to_reject(self):
        adapter = FakePerceptionModelAdapter(
            detections=(
                PerceptionDetection(
                    object_id="person_1",
                    class_name="person",
                    confidence=0.95,
                    zone="danger_zone",
                ),
            ),
        )
        request = PerceptionInferenceRequest(
            input_path=Path(__file__),
            sequence_id="escalate_test",
            frame_id="f1",
        )
        record = run_perception_inference(
            adapter=adapter,
            request=request,
            original_decision="approve",
            original_risk_level="low",
        )
        assert record.fusion_result["fused_decision"] == "reject"
        assert record.fusion_result["fused_risk_level"] == "high"

    def test_record_writer_creates_json(self, tmp_path):
        record = PerceptionInferenceRecord(
            adapter_name="FakeAdapter",
            adapter_kind="fake",
            input_path="/mock/path",
            input_exists=False,
            frame_id="f1",
        )
        out = tmp_path / "records" / "record.json"
        result = write_perception_inference_record(record, out)
        assert result == out
        assert out.exists()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["schema_version"] == "perception_inference_record.v1"
        assert loaded["adapter_name"] == "FakeAdapter"

    def test_manifest_includes_perception_artifact(self, tmp_path):
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({"episode_id": "ep_percept", "artifacts": []}), encoding="utf-8")
        record = PerceptionInferenceRecord(
            adapter_name="Test",
            adapter_kind="fake",
            input_path="/mock",
            input_exists=False,
            frame_id="f1",
        )
        rec_path = tmp_path / "perception_inference_record.json"
        write_perception_inference_record(record, rec_path)

        manifest = build_evidence_manifest(
            context_path=ctx,
            perception_record_path=rec_path,
        )
        kinds = {a["kind"] for a in manifest["artifacts"]}
        assert "perception_inference_record" in kinds

    def test_manifest_checks_perception_evidence(self, tmp_path):
        ctx = tmp_path / "ctx.json"
        ctx.write_text(json.dumps({"episode_id": "ep_chk", "artifacts": []}), encoding="utf-8")
        record = PerceptionInferenceRecord(adapter_name="T", adapter_kind="fake", input_path="/m", frame_id="f1")
        rec_path = tmp_path / "rec.json"
        write_perception_inference_record(record, rec_path)

        manifest = build_evidence_manifest(context_path=ctx, perception_record_path=rec_path)
        assert manifest["checks"]["has_perception_evidence"] is True
        assert manifest["checks"]["perception_record_valid"] is True

    def test_evidence_groups_perception_available(self, tmp_path):
        ctx = tmp_path / "ctx.json"
        ctx.write_text(json.dumps({"episode_id": "ep_grp", "artifacts": []}), encoding="utf-8")
        record = PerceptionInferenceRecord(adapter_name="T", adapter_kind="fake", input_path="/m", frame_id="f1")
        rec_path = tmp_path / "rec.json"
        write_perception_inference_record(record, rec_path)

        manifest = build_evidence_manifest(context_path=ctx, perception_record_path=rec_path)
        assert manifest["evidence_groups"]["perception"]["available"] is True

    def test_manifest_summary_has_fused_decision(self, tmp_path):
        adapter = FakePerceptionModelAdapter(
            detections=(
                PerceptionDetection(
                    object_id="person_1", class_name="person",
                    confidence=0.95, zone="danger_zone",
                ),
            ),
        )
        request = PerceptionInferenceRequest(input_path=Path(__file__), frame_id="f1")
        record = run_perception_inference(adapter=adapter, request=request, original_decision="approve")
        rec_path = tmp_path / "rec.json"
        write_perception_inference_record(record, rec_path)

        ctx = tmp_path / "ctx.json"
        ctx.write_text(json.dumps({"episode_id": "ep_fuse", "artifacts": []}), encoding="utf-8")
        manifest = build_evidence_manifest(context_path=ctx, perception_record_path=rec_path)
        assert manifest["summary"]["perception_fused_decision"] == "reject"
        assert manifest["summary"]["perception_adapter"] == "FakePerceptionModelAdapter"

    def test_expected_contract_requires_perception(self, tmp_path):
        ctx = tmp_path / "ctx.json"
        ctx.write_text(json.dumps({"episode_id": "ep_ct", "artifacts": []}), encoding="utf-8")
        record = PerceptionInferenceRecord(adapter_name="T", adapter_kind="fake", input_path="/m", frame_id="f1")
        rec_path = tmp_path / "rec.json"
        write_perception_inference_record(record, rec_path)

        manifest = build_evidence_manifest(context_path=ctx, perception_record_path=rec_path)
        actual = {"total_steps": 1}
        expected = {
            "required_artifacts": ["perception_inference_record", "evidence_manifest"],
            "required_evidence_groups": ["perception"],
        }
        passed, errors = validate_expected_contract(expected=expected, actual=actual, manifest=manifest)
        assert passed is True, f"Contract failed: {errors}"

    def test_no_perception_record_keeps_old_behavior(self, tmp_path):
        ctx = tmp_path / "ctx.json"
        ctx.write_text(json.dumps({"episode_id": "ep_old", "artifacts": []}), encoding="utf-8")
        manifest = build_evidence_manifest(context_path=ctx)
        assert manifest["checks"]["has_perception_evidence"] is False
        assert manifest["checks"]["perception_record_valid"] is False
        assert manifest["evidence_groups"]["perception"]["available"] is False

    def test_no_real_model_dependencies(self):
        import sys
        forbidden = {"onnxruntime", "torch", "ultralytics", "rknn", "cv2"}
        loaded = {m.split(".")[0] for m in sys.modules}
        assert not (forbidden & loaded), f"Found forbidden modules: {forbidden & loaded}"
