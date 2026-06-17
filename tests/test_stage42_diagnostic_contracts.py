import json
from pathlib import Path

import pytest

from application.diagnostic_contracts import (
    ExpectedContract,
    build_actual_summary,
    load_expected_contract,
    validate_expected_contract,
)


class TestLoadExpectedContract:
    def test_load_valid(self, tmp_path):
        contract_file = tmp_path / "expected_contract.json"
        contract_file.write_text(json.dumps({
            "schema_version": "expected_contract.v1",
            "case_id": "test_case",
            "expected": {"total_steps": 2},
        }), encoding="utf-8")

        contract = load_expected_contract(contract_file)
        assert isinstance(contract, ExpectedContract)
        assert contract.case_id == "test_case"
        assert contract.expected == {"total_steps": 2}

    def test_invalid_schema_version_raises(self, tmp_path):
        contract_file = tmp_path / "bad_schema.json"
        contract_file.write_text(json.dumps({
            "schema_version": "expected_contract.v0",
            "case_id": "test",
            "expected": {},
        }), encoding="utf-8")

        with pytest.raises(ValueError, match="expected_contract.v1"):
            load_expected_contract(contract_file)

    def test_missing_case_id_raises(self, tmp_path):
        contract_file = tmp_path / "no_case_id.json"
        contract_file.write_text(json.dumps({
            "schema_version": "expected_contract.v1",
            "expected": {},
        }), encoding="utf-8")

        with pytest.raises(ValueError, match="case_id"):
            load_expected_contract(contract_file)

    def test_missing_expected_dict_raises(self, tmp_path):
        contract_file = tmp_path / "no_expected.json"
        contract_file.write_text(json.dumps({
            "schema_version": "expected_contract.v1",
            "case_id": "test",
        }), encoding="utf-8")

        with pytest.raises(ValueError, match="expected"):
            load_expected_contract(contract_file)

    def test_non_dict_root_raises(self, tmp_path):
        contract_file = tmp_path / "list.json"
        contract_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

        with pytest.raises(ValueError, match="JSON object"):
            load_expected_contract(contract_file)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_expected_contract(tmp_path / "nonexistent.json")

    def test_invalid_json_raises(self, tmp_path):
        contract_file = tmp_path / "bad.json"
        contract_file.write_text("not json", encoding="utf-8")

        with pytest.raises(ValueError, match="invalid JSON"):
            load_expected_contract(contract_file)


class TestBuildActualSummary:
    def test_final_status_reject(self):
        context = {
            "total_steps": 3,
            "approved_steps": 1,
            "executed_steps": 1,
            "blocked_steps": 2,
            "rejected_steps": 1,
            "manual_review_steps": 0,
            "min_clearance": -0.05,
            "closest_robot_link": "link_3",
            "closest_obstacle": "obs_1",
            "worst_sequence_step_index": 2,
            "backend_worst_step": 3,
        }
        actual = build_actual_summary(context)
        assert actual["final_status"] == "reject"
        assert actual["total_steps"] == 3
        assert actual["rejected_steps"] == 1

    def test_final_status_manual_review(self):
        context = {
            "total_steps": 2,
            "approved_steps": 1,
            "rejected_steps": 0,
            "manual_review_steps": 1,
        }
        actual = build_actual_summary(context)
        assert actual["final_status"] == "manual_review"

    def test_final_status_approve(self):
        context = {
            "total_steps": 2,
            "approved_steps": 2,
            "rejected_steps": 0,
            "manual_review_steps": 0,
        }
        actual = build_actual_summary(context)
        assert actual["final_status"] == "approve"

    def test_zero_values_handled(self):
        """None/zero rejected and manual_review should not crash."""
        context = {"rejected_steps": None, "manual_review_steps": None}
        actual = build_actual_summary(context)
        assert actual["final_status"] == "approve"
        assert actual["rejected_steps"] == 0
        assert actual["manual_review_steps"] == 0


class TestValidateExpectedContract:
    def test_passes_all_fields(self):
        actual = {
            "total_steps": 3,
            "approved_steps": 2,
            "manual_review_steps": 1,
            "rejected_steps": 1,
            "final_status": "reject",
        }
        expected = {
            "total_steps": 3,
            "min_approved_steps": 1,
            "min_manual_review_steps": 1,
            "min_rejected_steps": 1,
            "expected_final_status": "reject",
        }
        passed, errors = validate_expected_contract(expected=expected, actual=actual)
        assert passed is True
        assert errors == ()

    def test_fails_total_steps_mismatch(self):
        actual = {"total_steps": 2}
        expected = {"total_steps": 3}
        passed, errors = validate_expected_contract(expected=expected, actual=actual)
        assert passed is False
        assert any("total_steps" in e for e in errors)

    def test_fails_min_approved_steps(self):
        actual = {"approved_steps": 0}
        expected = {"min_approved_steps": 1}
        passed, errors = validate_expected_contract(expected=expected, actual=actual)
        assert passed is False
        assert any("approved_steps" in e for e in errors)

    def test_fails_min_manual_review_steps(self):
        actual = {"manual_review_steps": 0}
        expected = {"min_manual_review_steps": 1}
        passed, errors = validate_expected_contract(expected=expected, actual=actual)
        assert passed is False
        assert any("manual_review_steps" in e for e in errors)

    def test_fails_min_rejected_steps(self):
        actual = {"rejected_steps": 0}
        expected = {"min_rejected_steps": 1}
        passed, errors = validate_expected_contract(expected=expected, actual=actual)
        assert passed is False
        assert any("rejected_steps" in e for e in errors)

    def test_fails_final_status_mismatch(self):
        actual = {"final_status": "approve"}
        expected = {"expected_final_status": "reject"}
        passed, errors = validate_expected_contract(expected=expected, actual=actual)
        assert passed is False
        assert any("final_status" in e for e in errors)

    def test_required_artifacts_check(self):
        manifest = {
            "artifacts": [
                {"kind": "diagnostic_context_json", "exists": True},
                {"kind": "deterministic_report", "exists": True},
            ]
        }
        actual = {"total_steps": 1}
        expected = {
            "required_artifacts": ["diagnostic_context_json", "deterministic_report"],
        }
        passed, errors = validate_expected_contract(expected=expected, actual=actual, manifest=manifest)
        assert passed is True

    def test_required_artifacts_missing(self):
        manifest = {
            "artifacts": [
                {"kind": "diagnostic_context_json", "exists": True},
            ]
        }
        actual = {"total_steps": 1}
        expected = {
            "required_artifacts": ["diagnostic_context_json", "nonexistent_artifact"],
        }
        passed, errors = validate_expected_contract(expected=expected, actual=actual, manifest=manifest)
        assert passed is False
        assert any("nonexistent_artifact" in e for e in errors)

    def test_no_expected_fields_returns_pass(self):
        actual = {"total_steps": 1}
        expected = {}
        passed, errors = validate_expected_contract(expected=expected, actual=actual)
        assert passed is True
        assert errors == ()

    def test_multiple_errors(self):
        actual = {"total_steps": 1, "approved_steps": 0, "rejected_steps": 0, "final_status": "approve"}
        expected = {"total_steps": 3, "min_approved_steps": 1, "min_rejected_steps": 1, "expected_final_status": "reject"}
        passed, errors = validate_expected_contract(expected=expected, actual=actual)
        assert passed is False
        assert len(errors) >= 2

    def test_evidence_manifest_in_required_artifacts_passes(self):
        """evidence_manifest is a special kind that always counts as existing."""
        manifest = {
            "artifacts": [
                {"kind": "diagnostic_context_json", "exists": True},
            ]
        }
        actual = {"total_steps": 1}
        expected = {
            "required_artifacts": ["diagnostic_context_json", "evidence_manifest"],
        }
        passed, errors = validate_expected_contract(expected=expected, actual=actual, manifest=manifest)
        assert passed is True
        assert errors == ()
