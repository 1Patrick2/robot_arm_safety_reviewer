import pytest

from perception.models import SafetyObservation
from perception.fusion import fuse_safety_with_perception


class TestFuseSafetyWithPerception:
    def test_approve_without_observations_stays_approve(self):
        result = fuse_safety_with_perception(
            original_decision="approve",
            original_risk_level="low",
            observations=(),
        )
        assert result.fused_decision == "approve"
        assert result.fused_risk_level == "low"
        assert result.triggered_observations == ()

    def test_reject_is_never_downgraded(self):
        obs = SafetyObservation(
            kind="human_in_warning_zone",
            object_id="person_1",
            severity="medium",
            frame_id="f1",
            evidence_refs=("perception.frames[0].detections[0].zone",),
        )
        result = fuse_safety_with_perception(
            original_decision="reject",
            original_risk_level="high",
            observations=(obs,),
        )
        assert result.fused_decision == "reject"
        assert result.fused_risk_level == "high"
        assert result.triggered_observations == ()

    def test_human_warning_zone_escalates_approve_to_manual_review(self):
        obs = SafetyObservation(
            kind="human_in_warning_zone",
            object_id="person_1",
            severity="medium",
            frame_id="f1",
            evidence_refs=("perception.frames[0].detections[0].zone",),
        )
        result = fuse_safety_with_perception(
            original_decision="approve",
            original_risk_level="low",
            observations=(obs,),
        )
        assert result.fused_decision == "manual_review"
        assert result.fused_risk_level == "medium"
        assert result.triggered_observations == (obs,)

    def test_human_danger_zone_escalates_to_reject(self):
        obs = SafetyObservation(
            kind="human_in_danger_zone",
            object_id="person_1",
            severity="high",
            frame_id="f1",
            evidence_refs=("perception.frames[0].detections[0].zone",),
        )
        result = fuse_safety_with_perception(
            original_decision="approve",
            original_risk_level="low",
            observations=(obs,),
        )
        assert result.fused_decision == "reject"
        assert result.fused_risk_level == "high"

    def test_human_danger_zone_escalates_manual_review_to_reject(self):
        obs = SafetyObservation(
            kind="human_in_danger_zone",
            object_id="person_1",
            severity="high",
            frame_id="f1",
            evidence_refs=("perception.frames[0].detections[0].zone",),
        )
        result = fuse_safety_with_perception(
            original_decision="manual_review",
            original_risk_level="medium",
            observations=(obs,),
        )
        assert result.fused_decision == "reject"
        assert result.fused_risk_level == "high"

    def test_low_confidence_escalates_approve_to_manual_review(self):
        obs = SafetyObservation(
            kind="low_confidence_detection",
            object_id="obs_1",
            severity="low",
            frame_id="f1",
            evidence_refs=("perception.frames[0].detections[0].confidence",),
        )
        result = fuse_safety_with_perception(
            original_decision="approve",
            original_risk_level="low",
            observations=(obs,),
        )
        assert result.fused_decision == "manual_review"
        assert result.fused_risk_level == "medium"

    def test_object_danger_zone_escalates_to_manual_review(self):
        obs = SafetyObservation(
            kind="object_in_danger_zone",
            object_id="box_1",
            severity="high",
            frame_id="f1",
            evidence_refs=("perception.frames[0].detections[0].zone",),
        )
        result = fuse_safety_with_perception(
            original_decision="approve",
            original_risk_level="low",
            observations=(obs,),
        )
        assert result.fused_decision == "manual_review"
        assert result.fused_risk_level == "medium"

    def test_evidence_refs_are_propagated_from_triggered_observations(self):
        obs1 = SafetyObservation(
            kind="human_in_danger_zone",
            object_id="person_1",
            severity="high",
            frame_id="f1",
            evidence_refs=("a", "b"),
        )
        obs2 = SafetyObservation(
            kind="human_in_danger_zone",
            object_id="person_2",
            severity="high",
            frame_id="f1",
            evidence_refs=("b", "c"),
        )
        result = fuse_safety_with_perception(
            original_decision="approve",
            observations=(obs1, obs2),
        )
        assert result.evidence_refs == ("a", "b", "c")

    def test_invalid_original_decision_fails(self):
        with pytest.raises(ValueError, match="unsupported original_decision"):
            fuse_safety_with_perception(
                original_decision="unknown",
                observations=(),
            )

    def test_result_to_dict_shape(self):
        obs = SafetyObservation(
            kind="human_in_danger_zone",
            object_id="person_1",
            severity="high",
            frame_id="f1",
            evidence_refs=("p.f[0].zone",),
        )
        result = fuse_safety_with_perception(
            original_decision="approve",
            original_risk_level="low",
            observations=(obs,),
        )
        d = result.to_dict()
        assert d["schema_version"] == "perception_safety_fusion_result.v1"
        assert d["original_decision"] == "approve"
        assert d["fused_decision"] == "reject"
        assert isinstance(d["triggered_observations"], list)
        assert isinstance(d["evidence_refs"], list)
        assert d["triggered_observations"][0]["kind"] == "human_in_danger_zone"

    def test_manual_review_with_warning_zone_stays_manual_review(self):
        obs = SafetyObservation(
            kind="human_in_warning_zone",
            object_id="person_1",
            severity="medium",
            frame_id="f1",
            evidence_refs=("perception.frames[0].detections[0].zone",),
        )
        result = fuse_safety_with_perception(
            original_decision="manual_review",
            original_risk_level="medium",
            observations=(obs,),
        )
        assert result.fused_decision == "manual_review"
        assert result.fused_risk_level == "medium"
        assert result.triggered_observations == (obs,)

    def test_unknown_object_detected_escalates_to_manual_review(self):
        obs = SafetyObservation(
            kind="unknown_object_detected",
            object_id="unk_1",
            severity="high",
            frame_id="f1",
            evidence_refs=("perception.frames[0].detections[0].zone",),
        )
        result = fuse_safety_with_perception(
            original_decision="approve",
            original_risk_level="low",
            observations=(obs,),
        )
        assert result.fused_decision == "manual_review"
        assert result.fused_risk_level == "medium"
        assert result.triggered_observations == (obs,)

    def test_close_object_detected_escalates_to_manual_review(self):
        obs = SafetyObservation(
            kind="close_object_detected",
            object_id="obs_1",
            severity="medium",
            frame_id="f1",
            evidence_refs=("perception.frames[0].detections[0].distance_m",),
        )
        result = fuse_safety_with_perception(
            original_decision="approve",
            original_risk_level="low",
            observations=(obs,),
        )
        assert result.fused_decision == "manual_review"
        assert result.fused_risk_level == "medium"
        assert result.triggered_observations == (obs,)

    def test_non_triggering_observation_does_not_enter_triggered(self):
        """Observations that are present but do not change the decision must not
        appear in triggered_observations."""
        obs = SafetyObservation(
            kind="object_in_warning_zone",
            object_id="box_1",
            severity="medium",
            frame_id="f1",
            evidence_refs=("perception.frames[0].detections[0].zone",),
        )
        # original is reject -> no observation can change it
        result = fuse_safety_with_perception(
            original_decision="reject",
            observations=(obs,),
        )
        assert result.fused_decision == "reject"
        assert result.triggered_observations == ()
