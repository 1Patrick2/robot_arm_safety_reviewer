from __future__ import annotations

import json
from pathlib import Path

import pytest

from perception.loader import load_perception_result
from perception.fake_adapter import build_safety_observations
from perception.fusion import fuse_safety_with_perception

ROOT = Path(__file__).resolve().parents[1]
CASES_ROOT = ROOT / "bench" / "perception_safety_scenarios"

CASE_IDS = (
    "human_near_workspace_sequence",
    "human_enter_danger_zone_sequence",
    "low_confidence_detection_sequence",
)


def _load_contract(case_dir: Path) -> dict:
    data = json.loads((case_dir / "expected_contract.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "perception_expected_contract.v1"
    assert data["case_id"] == case_dir.name
    return data


def _compute_decision_from_steps(
    approved: int, rejected: int, manual_review: int,
) -> tuple[str, str | None]:
    """Determine the overall decision and risk level from step counts."""
    if rejected > 0:
        return "reject", "high"
    if manual_review > 0:
        return "manual_review", "medium"
    return "approve", "low"


def _run_original_decision(case_dir: Path) -> tuple[str, str | None]:
    """Run the deterministic sandbox for a case and return (decision, risk_level).

    Uses ``run_sandbox`` from the application layer — same pipeline
    as the existing diagnostic regression.
    """
    from application.sandbox_service import SandboxRunRequest, run_sandbox

    result = run_sandbox(SandboxRunRequest(
        sequence_path=case_dir / "sequence.json",
        scene_path=case_dir / "scene.json",
        backend_name="mock",
    ))

    runtime = result.sequence_runtime_result
    return _compute_decision_from_steps(
        approved=runtime.approved_steps,
        rejected=runtime.rejected_steps,
        manual_review=runtime.manual_review_steps,
    )


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_perception_case_files_exist(case_id):
    case_dir = CASES_ROOT / case_id
    assert (case_dir / "scene.json").exists(), f"Missing scene.json for {case_id}"
    assert (case_dir / "sequence.json").exists(), f"Missing sequence.json for {case_id}"
    assert (case_dir / "perception_result.json").exists(), f"Missing perception_result.json for {case_id}"
    assert (case_dir / "expected_contract.json").exists(), f"Missing expected_contract.json for {case_id}"


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_perception_case_matches_expected_fusion_contract(case_id, tmp_path):
    case_dir = CASES_ROOT / case_id
    contract = _load_contract(case_dir)

    # Run deterministic pipeline to get actual original decision
    original_decision, original_risk_level = _run_original_decision(case_dir)
    assert original_decision == contract["expected_original_decision"], (
        f"Original decision mismatch for {case_id}: "
        f"expected {contract['expected_original_decision']}, got {original_decision}"
    )

    # Load perception result and build observations
    perception = load_perception_result(case_dir / "perception_result.json")
    observations = build_safety_observations(perception)

    # Fuse
    fused = fuse_safety_with_perception(
        original_decision=original_decision,
        original_risk_level=original_risk_level,
        observations=observations,
    )

    # Check fused decision
    assert fused.fused_decision == contract["expected_fused_decision"], (
        f"Fused decision mismatch for {case_id}: "
        f"expected {contract['expected_fused_decision']}, got {fused.fused_decision}"
    )
    assert fused.fused_risk_level == contract["expected_fused_risk_level"], (
        f"Fused risk level mismatch for {case_id}: "
        f"expected {contract['expected_fused_risk_level']}, got {fused.fused_risk_level}"
    )

    # Check required observation kinds
    kinds = {o.kind for o in observations}
    for kind in contract.get("required_observation_kinds", []):
        assert kind in kinds, f"{case_id}: missing required observation kind '{kind}'"

    # Check forbidden observation kinds
    for kind in contract.get("forbidden_observation_kinds", []):
        assert kind not in kinds, f"{case_id}: unexpected observation kind '{kind}'"

    # Check required evidence refs (check either fused refs or observation refs)
    for ref in contract.get("required_evidence_refs", []):
        assert (
            ref in fused.evidence_refs
            or any(ref in o.evidence_refs for o in observations)
        ), f"{case_id}: missing required evidence ref '{ref}'"


def test_perception_fusion_result_to_dict():
    case_dir = CASES_ROOT / "human_near_workspace_sequence"
    original_decision, original_risk_level = _run_original_decision(case_dir)
    perception = load_perception_result(case_dir / "perception_result.json")
    observations = build_safety_observations(perception)
    fused = fuse_safety_with_perception(
        original_decision=original_decision,
        original_risk_level=original_risk_level,
        observations=observations,
    )
    d = fused.to_dict()
    assert d["schema_version"] == "perception_safety_fusion_result.v1"
    assert d["original_decision"] == original_decision
    assert d["fused_decision"] == fused.fused_decision
    assert isinstance(d["triggered_observations"], list)
    assert isinstance(d["evidence_refs"], list)
