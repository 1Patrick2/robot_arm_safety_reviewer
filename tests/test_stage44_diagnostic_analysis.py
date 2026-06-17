from diagnostic_runtime.analysis.models import DiagnosticAnalysis, RootCauseHypothesis
from diagnostic_runtime.analysis.fake_analyst import run_fake_diagnostic_analyst
from diagnostic_runtime.analysis.evidence_refs import (
    collect_available_evidence_kinds,
    collect_available_evidence_groups,
    build_basic_evidence_refs,
)


class TestDiagnosticAnalysisModels:
    def test_root_cause_hypothesis_to_dict(self):
        h = RootCauseHypothesis(
            hypothesis="test",
            evidence_refs=("ref1", "ref2"),
            confidence="medium",
        )
        d = h.to_dict()
        assert d["hypothesis"] == "test"
        assert d["evidence_refs"] == ["ref1", "ref2"]
        assert d["confidence"] == "medium"

    def test_diagnostic_analysis_default_schema_version(self):
        a = DiagnosticAnalysis()
        assert a.schema_version == "llm_diagnostic_analysis.v1"
        assert a.analysis_mode == "fake"

    def test_diagnostic_analysis_to_dict_shape(self):
        a = DiagnosticAnalysis(
            case_id="case_1",
            episode_id="ep_1",
            deterministic_outcome={"final_status": "approve"},
            risk_summary="All good.",
            root_cause_hypotheses=(RootCauseHypothesis("h1", ("r1",), "low"),),
            evidence_used=("ctx",),
            uncertainties=("none",),
        )
        d = a.to_dict()
        assert d["schema_version"] == "llm_diagnostic_analysis.v1"
        assert d["case_id"] == "case_1"
        assert d["episode_id"] == "ep_1"
        assert d["analysis_mode"] == "fake"
        assert d["deterministic_outcome"] == {"final_status": "approve"}
        assert d["risk_summary"] == "All good."
        assert len(d["root_cause_hypotheses"]) == 1
        assert d["evidence_used"] == ["ctx"]
        assert d["uncertainties"] == ["none"]
        assert d["prohibited_actions_detected"] == []


class TestEvidenceRefs:
    def test_collect_kinds_returns_evidence_manifest_by_default(self):
        manifest = {}
        kinds = collect_available_evidence_kinds(manifest)
        assert "evidence_manifest" in kinds

    def test_collect_kinds_includes_existing_artifacts(self):
        manifest = {
            "artifacts": [
                {"kind": "diagnostic_context_json", "exists": True},
                {"kind": "missing_file", "exists": False},
            ]
        }
        kinds = collect_available_evidence_kinds(manifest)
        assert "diagnostic_context_json" in kinds
        assert "missing_file" not in kinds

    def test_collect_kinds_missing_artifacts_returns_just_manifest(self):
        manifest = {}
        kinds = collect_available_evidence_kinds(manifest)
        assert kinds == {"evidence_manifest"}

    def test_collect_groups_returns_available(self):
        manifest = {
            "evidence_groups": {
                "geometry": {"available": True},
                "safety": {"available": False},
            }
        }
        groups = collect_available_evidence_groups(manifest)
        assert "geometry" in groups
        assert "safety" not in groups

    def test_collect_groups_missing_returns_empty(self):
        assert collect_available_evidence_groups({}) == set()

    def test_build_basic_refs_includes_present_fields_and_available_groups(self):
        manifest = {
            "evidence_groups": {
                "geometry": {"available": True},
                "safety": {"available": True},
            }
        }
        summary = {
            "min_clearance": 0.08,
            "closest_obstacle": "sphere_near",
            "closest_robot_link": "link_3",
            "worst_sequence_step_index": 2,
        }
        refs = build_basic_evidence_refs(manifest, summary)
        assert "summary.min_clearance" in refs
        assert "summary.closest_obstacle" in refs
        assert "summary.closest_robot_link" in refs
        assert "summary.worst_sequence_step_index" in refs
        assert "evidence_groups.geometry" in refs
        assert "evidence_groups.safety" in refs

    def test_build_basic_refs_omits_none_fields(self):
        manifest = {"evidence_groups": {"geometry": {"available": True}}}
        summary = {"min_clearance": None, "closest_obstacle": "sphere"}
        refs = build_basic_evidence_refs(manifest, summary)
        assert "summary.min_clearance" not in refs
        assert "summary.closest_obstacle" in refs


class TestFakeDiagnosticAnalyst:
    def test_fake_analyst_returns_schema_v1(self):
        context = {"episode_id": "ep1", "sequence_id": "s1"}
        manifest = {
            "evidence_groups": {
                "geometry": {"available": True},
                "safety": {"available": True},
            }
        }
        analysis = run_fake_diagnostic_analyst(context=context, manifest=manifest)
        assert analysis.schema_version == "llm_diagnostic_analysis.v1"
        assert analysis.analysis_mode == "fake"

    def test_rejected_context_produces_reject_risk_summary(self):
        context = {
            "episode_id": "ep1",
            "sequence_id": "case_reject",
            "total_steps": 2,
            "approved_steps": 0,
            "manual_review_steps": 0,
            "rejected_steps": 1,
            "min_clearance": -0.01,
            "closest_obstacle": "sphere_mid",
            "closest_robot_link": "link_3",
            "worst_sequence_step_index": 1,
        }
        manifest = {
            "evidence_groups": {
                "geometry": {"available": True},
                "safety": {"available": True},
            }
        }
        analysis = run_fake_diagnostic_analyst(context=context, manifest=manifest)
        assert "rejected" in analysis.risk_summary.lower() or "reject" in analysis.risk_summary.lower()
        assert analysis.deterministic_outcome["final_status"] == "reject"

    def test_hypotheses_include_evidence_refs(self):
        context = {
            "episode_id": "ep1",
            "min_clearance": 0.05,
            "closest_obstacle": "sphere",
            "closest_robot_link": "link_2",
        }
        manifest = {
            "evidence_groups": {
                "geometry": {"available": True},
                "safety": {"available": True},
            }
        }
        analysis = run_fake_diagnostic_analyst(context=context, manifest=manifest)
        for h in analysis.root_cause_hypotheses:
            assert h.evidence_refs, f"Hypothesis missing evidence_refs: {h.hypothesis}"
            for ref in h.evidence_refs:
                assert isinstance(ref, str)

    def test_fake_analyst_does_not_claim_prohibited_actions(self):
        context = {"episode_id": "ep1"}
        manifest = {"evidence_groups": {}}
        analysis = run_fake_diagnostic_analyst(context=context, manifest=manifest)
        assert analysis.prohibited_actions_detected == ()

    def test_fake_analyst_does_not_reference_unavailable_geometry_group(self):
        context = {
            "episode_id": "ep1",
            "sequence_id": "case_geom_unavailable",
            "min_clearance": 0.05,
            "closest_obstacle": "sphere",
            "closest_robot_link": "link_2",
        }
        manifest = {
            "evidence_groups": {
                "geometry": {"available": False},
                "safety": {"available": True},
            }
        }
        analysis = run_fake_diagnostic_analyst(context=context, manifest=manifest)
        refs = [ref for h in analysis.root_cause_hypotheses for ref in h.evidence_refs]
        assert "evidence_groups.geometry" not in refs
        assert any("Geometry evidence is unavailable" in u for u in analysis.uncertainties)
        assert all(h.evidence_refs for h in analysis.root_cause_hypotheses)
