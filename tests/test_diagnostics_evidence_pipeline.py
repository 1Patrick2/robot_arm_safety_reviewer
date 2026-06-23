"""Capability test: diagnostics evidence pipeline — manifest, contract, groups."""

import json
from pathlib import Path


def test_evidence_manifest_basic(tmp_path):
    from diagnostics.evidence.manifest import build_evidence_manifest
    ctx = tmp_path / "diagnostic_context.json"
    ctx.write_text(json.dumps({"episode_id": "ep1", "total_steps": 2, "approved_steps": 2, "artifacts": []}), encoding="utf-8")
    report = tmp_path / "report.md"
    report.write_text("# R", encoding="utf-8")
    trace = tmp_path / "trace.json"
    trace.write_text("{}", encoding="utf-8")
    manifest = build_evidence_manifest(context_path=ctx, deterministic_report_path=report, trace_path=trace)
    assert manifest["schema_version"] == "evidence_manifest.v1"
    assert manifest["episode_id"] == "ep1"
    assert manifest["checks"]["has_diagnostic_context"] is True
    assert manifest["checks"]["has_diagnostic_report"] is True
    assert manifest["checks"]["has_trace"] is True
    assert "evidence_groups" in manifest


def test_expected_contract_validation():
    from diagnostics.contracts.expected import validate_expected_contract
    actual = {"total_steps": 2, "approved_steps": 2, "rejected_steps": 0, "final_status": "approve"}
    expected = {"total_steps": 2, "min_approved_steps": 1, "expected_final_status": "approve"}
    passed, errors = validate_expected_contract(expected=expected, actual=actual)
    assert passed is True
    assert errors == ()


def test_expected_contract_fails_on_mismatch():
    from diagnostics.contracts.expected import validate_expected_contract
    actual = {"total_steps": 1, "rejected_steps": 0, "final_status": "approve"}
    expected = {"total_steps": 2, "expected_final_status": "reject"}
    passed, errors = validate_expected_contract(expected=expected, actual=actual)
    assert passed is False


def test_evidence_groups_contain_expected_keys(tmp_path):
    from diagnostics.evidence.manifest import build_evidence_manifest
    ctx = tmp_path / "ctx.json"
    ctx.write_text(json.dumps({"episode_id": "ep2", "total_steps": 1, "approved_steps": 1, "artifacts": []}), encoding="utf-8")
    report = tmp_path / "r.md"
    report.write_text("#", encoding="utf-8")
    trace = tmp_path / "t.json"
    trace.write_text("{}", encoding="utf-8")
    manifest = build_evidence_manifest(context_path=ctx, deterministic_report_path=report, trace_path=trace)
    groups = manifest["evidence_groups"]
    for g in ("runtime", "safety", "geometry", "diagnostic", "perception", "external_trajectory"):
        assert g in groups, f"Missing evidence group: {g}"


def test_required_evidence_groups_validation(tmp_path):
    from diagnostics.evidence.manifest import build_evidence_manifest
    from diagnostics.contracts.expected import validate_expected_contract
    ctx = tmp_path / "ctx.json"
    ctx.write_text(json.dumps({"episode_id": "ep3", "total_steps": 1, "approved_steps": 1, "artifacts": []}), encoding="utf-8")
    report = tmp_path / "r.md"
    report.write_text("#", encoding="utf-8")
    trace = tmp_path / "t.json"
    trace.write_text("{}", encoding="utf-8")
    manifest = build_evidence_manifest(context_path=ctx, deterministic_report_path=report, trace_path=trace)
    actual = {"total_steps": 1}
    expected = {"required_evidence_groups": ["runtime", "diagnostic"]}
    passed, errors = validate_expected_contract(expected=expected, actual=actual, manifest=manifest)
    assert passed is True, f"errors={errors}"
