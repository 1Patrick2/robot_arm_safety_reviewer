import json
from copy import deepcopy
from pathlib import Path

import pytest

from perception.models import (
    PerceptionDetection,
    PerceptionFrame,
    PerceptionResult,
    SafetyObservation,
)
from perception.loader import load_perception_result
from perception.fake_adapter import build_safety_observations


def _write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


_VALID_PERCEPTION = {
    "schema_version": "perception_result.v1",
    "sequence_id": "human_near_workspace_sequence",
    "frames": [
        {
            "frame_id": "frame_0001",
            "timestamp": "2026-06-17T10:00:00Z",
            "detections": [
                {
                    "object_id": "person_1",
                    "class_name": "person",
                    "confidence": 0.92,
                    "bbox_xyxy": [120, 80, 300, 420],
                    "zone": "warning_zone",
                    "distance_m": 0.75,
                }
            ],
        }
    ],
}


class TestLoadPerceptionResult:
    def test_load_valid(self, tmp_path):
        p = _write_json(tmp_path / "valid.json", _VALID_PERCEPTION)
        result = load_perception_result(p)
        assert result.schema_version == "perception_result.v1"
        assert result.sequence_id == "human_near_workspace_sequence"
        assert len(result.frames) == 1
        assert len(result.frames[0].detections) == 1
        assert result.frames[0].detections[0].class_name == "person"

    def test_missing_schema_version_fails(self, tmp_path):
        data = dict(_VALID_PERCEPTION)
        data.pop("schema_version")
        p = _write_json(tmp_path / "no_sv.json", data)
        with pytest.raises(ValueError, match="schema_version"):
            load_perception_result(p)

    def test_wrong_schema_version_fails(self, tmp_path):
        data = dict(_VALID_PERCEPTION)
        data["schema_version"] = "perception_result.v0"
        p = _write_json(tmp_path / "bad_sv.json", data)
        with pytest.raises(ValueError, match="schema_version"):
            load_perception_result(p)

    def test_detection_missing_class_name_fails(self, tmp_path):
        data = deepcopy(_VALID_PERCEPTION)
        data["frames"][0]["detections"][0].pop("class_name")
        p = _write_json(tmp_path / "no_cls.json", data)
        with pytest.raises(ValueError, match="class_name"):
            load_perception_result(p)

    def test_detection_confidence_out_of_range_fails(self, tmp_path):
        data = deepcopy(_VALID_PERCEPTION)
        data["frames"][0]["detections"][0]["confidence"] = 1.5
        p = _write_json(tmp_path / "bad_conf.json", data)
        with pytest.raises(ValueError, match="confidence"):
            load_perception_result(p)

    def test_detection_confidence_negative_fails(self, tmp_path):
        data = deepcopy(_VALID_PERCEPTION)
        data["frames"][0]["detections"][0]["confidence"] = -0.1
        p = _write_json(tmp_path / "neg_conf.json", data)
        with pytest.raises(ValueError, match="confidence"):
            load_perception_result(p)

    def test_non_dict_root_fails(self, tmp_path):
        p = _write_json(tmp_path / "list.json", [1, 2, 3])
        with pytest.raises(ValueError, match="JSON object"):
            load_perception_result(p)

    def test_missing_file_fails(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_perception_result(tmp_path / "nonexistent.json")

    def test_invalid_json_fails(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json", encoding="utf-8")
        with pytest.raises(ValueError, match="invalid JSON"):
            load_perception_result(p)

    def test_bbox_must_be_4_numbers(self, tmp_path):
        data = deepcopy(_VALID_PERCEPTION)
        data["frames"][0]["detections"][0]["bbox_xyxy"] = [1, 2, 3]
        p = _write_json(tmp_path / "bad_bbox.json", data)
        with pytest.raises(ValueError, match="bbox_xyxy"):
            load_perception_result(p)

    def test_distance_negative_fails(self, tmp_path):
        data = deepcopy(_VALID_PERCEPTION)
        data["frames"][0]["detections"][0]["distance_m"] = -1
        p = _write_json(tmp_path / "neg_dist.json", data)
        with pytest.raises(ValueError, match="distance_m"):
            load_perception_result(p)


class TestBuildSafetyObservations:
    def test_person_warning_zone_generates_human_warning_observation(self):
        perception = PerceptionResult(
            frames=(
                PerceptionFrame(
                    frame_id="f1",
                    detections=(
                        PerceptionDetection(
                            object_id="person_1",
                            class_name="person",
                            confidence=0.92,
                            zone="warning_zone",
                        ),
                    ),
                ),
            ),
        )
        obs = build_safety_observations(perception)
        kinds = {o.kind for o in obs}
        assert "human_in_warning_zone" in kinds
        for o in obs:
            if o.kind == "human_in_warning_zone":
                assert o.severity == "medium"
                assert o.evidence_refs

    def test_person_danger_zone_generates_human_danger_observation(self):
        perception = PerceptionResult(
            frames=(
                PerceptionFrame(
                    frame_id="f1",
                    detections=(
                        PerceptionDetection(
                            object_id="person_1",
                            class_name="person",
                            confidence=0.92,
                            zone="danger_zone",
                        ),
                    ),
                ),
            ),
        )
        obs = build_safety_observations(perception)
        kinds = {o.kind for o in obs}
        assert "human_in_danger_zone" in kinds
        for o in obs:
            if o.kind == "human_in_danger_zone":
                assert o.severity == "high"

    def test_low_confidence_generates_observation(self):
        perception = PerceptionResult(
            frames=(
                PerceptionFrame(
                    frame_id="f1",
                    detections=(
                        PerceptionDetection(
                            object_id="obs_1",
                            class_name="obstacle",
                            confidence=0.3,
                        ),
                    ),
                ),
            ),
        )
        obs = build_safety_observations(perception)
        kinds = {o.kind for o in obs}
        assert "low_confidence_detection" in kinds

    def test_close_distance_generates_observation(self):
        perception = PerceptionResult(
            frames=(
                PerceptionFrame(
                    frame_id="f1",
                    detections=(
                        PerceptionDetection(
                            object_id="obs_1",
                            class_name="obstacle",
                            confidence=0.9,
                            distance_m=0.2,
                        ),
                    ),
                ),
            ),
        )
        obs = build_safety_observations(perception)
        kinds = {o.kind for o in obs}
        assert "close_object_detected" in kinds
        for o in obs:
            if o.kind == "close_object_detected":
                assert o.severity == "high"

    def test_object_in_warning_zone(self):
        perception = PerceptionResult(
            frames=(
                PerceptionFrame(
                    frame_id="f1",
                    detections=(
                        PerceptionDetection(
                            object_id="box_1",
                            class_name="obstacle",
                            confidence=0.85,
                            zone="warning_zone",
                        ),
                    ),
                ),
            ),
        )
        obs = build_safety_observations(perception)
        kinds = {o.kind for o in obs}
        assert "object_in_warning_zone" in kinds

    def test_object_in_danger_zone(self):
        perception = PerceptionResult(
            frames=(
                PerceptionFrame(
                    frame_id="f1",
                    detections=(
                        PerceptionDetection(
                            object_id="box_1",
                            class_name="obstacle",
                            confidence=0.85,
                            zone="danger_zone",
                        ),
                    ),
                ),
            ),
        )
        obs = build_safety_observations(perception)
        kinds = {o.kind for o in obs}
        assert "object_in_danger_zone" in kinds

    def test_unknown_object_in_danger_zone(self):
        perception = PerceptionResult(
            frames=(
                PerceptionFrame(
                    frame_id="f1",
                    detections=(
                        PerceptionDetection(
                            object_id="unk_1",
                            class_name="unknown",
                            confidence=0.6,
                            zone="danger_zone",
                        ),
                    ),
                ),
            ),
        )
        obs = build_safety_observations(perception)
        kinds = {o.kind for o in obs}
        assert "unknown_object_detected" in kinds
        for o in obs:
            if o.kind == "unknown_object_detected":
                assert o.severity == "high"

    def test_all_observations_have_evidence_refs(self):
        perception = PerceptionResult(
            frames=(
                PerceptionFrame(
                    frame_id="f1",
                    detections=(
                        PerceptionDetection(
                            object_id="person_1",
                            class_name="person",
                            confidence=0.92,
                            zone="danger_zone",
                            distance_m=0.3,
                        ),
                    ),
                ),
            ),
        )
        obs = build_safety_observations(perception)
        assert obs
        for o in obs:
            assert o.evidence_refs, f"Observation {o.kind} missing evidence_refs"
