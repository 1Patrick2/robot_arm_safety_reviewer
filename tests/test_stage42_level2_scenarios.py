import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LEVEL2 = ROOT / "bench" / "level2_safety_scenarios"

LEVEL2_CASE_IDS = [
    "near_threshold_clearance_sequence",
    "midpoint_collision_sequence",
    "mixed_decision_sequence",
]


def _level2_cases():
    """Build DiagnosticRegressionCase tuples for all Level-2 scenarios."""
    from application.diagnostic_service import DiagnosticRegressionCase

    return tuple(
        DiagnosticRegressionCase(
            case_id=cid,
            sequence_path=LEVEL2 / cid / "sequence.json",
            scene_path=LEVEL2 / cid / "scene.json",
            expected_contract_path=LEVEL2 / cid / "expected_contract.json",
        )
        for cid in LEVEL2_CASE_IDS
    )


class TestLevel2CaseFiles:
    def test_all_case_directories_exist(self):
        for cid in LEVEL2_CASE_IDS:
            case_dir = LEVEL2 / cid
            assert case_dir.is_dir(), f"missing case directory: {case_dir}"

    def test_each_case_has_required_files(self):
        required = ["scene.json", "sequence.json", "expected_contract.json"]
        for cid in LEVEL2_CASE_IDS:
            case_dir = LEVEL2 / cid
            for filename in required:
                fpath = case_dir / filename
                assert fpath.exists(), f"missing {filename} in {case_dir}"


class TestLevel2ExpectedContracts:
    def test_all_contracts_load(self):
        from application.diagnostic_contracts import load_expected_contract

        for cid in LEVEL2_CASE_IDS:
            contract = load_expected_contract(LEVEL2 / cid / "expected_contract.json")
            assert contract.case_id == cid
            assert isinstance(contract.expected, dict)
            assert "total_steps" in contract.expected
            assert "required_artifacts" in contract.expected

    def test_contract_schema_versions_are_v1(self):
        from application.diagnostic_contracts import load_expected_contract

        for cid in LEVEL2_CASE_IDS:
            contract = load_expected_contract(LEVEL2 / cid / "expected_contract.json")
            assert contract.case_id == cid


class TestLevel2Regression:
    def test_level2_regression_contracts_pass(self):
        """All Level-2 cases must pass pipeline, evidence, and contract checks."""
        from application.diagnostic_service import (
            DiagnosticRegressionRequest,
            run_diagnostic_regression,
        )

        result = run_diagnostic_regression(
            DiagnosticRegressionRequest(
                cases=_level2_cases(),
                output_dir=ROOT / "output_reports" / "stage42_level2_test",
                stop_on_block=False,
            )
        )

        assert result.total_cases == 3
        assert result.passed_cases == 3
        assert result.failed_cases == 0

        for case in result.case_results:
            assert case.ok is True, f"{case.case_id}: ok=False"
            assert case.pipeline_passed is True, f"{case.case_id}: pipeline not passed"
            assert case.evidence_complete is True, f"{case.case_id}: evidence not complete"
            assert case.contract_passed is True, f"{case.case_id}: contract not passed"
            assert case.expected is not None, f"{case.case_id}: expected is None"
            assert case.actual is not None, f"{case.case_id}: actual is None"
            assert case.evidence_manifest_path is not None
            assert case.evidence_manifest_path.exists()
            assert case.errors == (), f"{case.case_id}: errors={case.errors}"

    def test_level2_manifest_contains_structured_visual_data(self):
        """Evidence manifest for each case must index trajectory_overview_data."""
        from application.diagnostic_service import (
            DiagnosticRegressionRequest,
            run_diagnostic_regression,
        )

        result = run_diagnostic_regression(
            DiagnosticRegressionRequest(
                cases=_level2_cases(),
                output_dir=ROOT / "output_reports" / "stage42_level2_manifest_test",
                stop_on_block=False,
            )
        )

        for case in result.case_results:
            manifest = json.loads(
                Path(case.evidence_manifest_path).read_text(encoding="utf-8")
            )
            kinds = {a["kind"] for a in manifest["artifacts"]}
            assert "trajectory_overview_data" in kinds, f"{case.case_id}: missing trajectory_overview_data"
            assert manifest["checks"]["has_structured_visual_data"] is True

    def test_level2_cases_are_not_all_approve(self):
        """Level-2 cases must include reject and manual_review outcomes."""
        from application.diagnostic_service import (
            DiagnosticRegressionRequest,
            run_diagnostic_regression,
        )

        result = run_diagnostic_regression(
            DiagnosticRegressionRequest(
                cases=_level2_cases(),
                output_dir=ROOT / "output_reports" / "stage42_level2_diversity_test",
                stop_on_block=False,
            )
        )

        statuses = {case.actual["final_status"] for case in result.case_results}
        assert "reject" in statuses, "No case produced reject status"

        has_manual = "manual_review" in statuses or any(
            case.actual["manual_review_steps"] > 0 for case in result.case_results
        )
        assert has_manual, "No case produced manual_review"
