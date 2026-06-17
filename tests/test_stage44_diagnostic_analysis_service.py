import json
from pathlib import Path

import pytest

from application.diagnostic_analysis_service import (
    DiagnosticAnalysisRequest,
    DiagnosticAnalysisResult,
    run_diagnostic_analysis,
)


class TestDiagnosticAnalysisService:
    def test_writes_analysis_json(self, tmp_path):
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep1",
            "sequence_id": "case1",
            "total_steps": 2,
            "approved_steps": 0,
            "manual_review_steps": 0,
            "rejected_steps": 1,
            "min_clearance": -0.01,
            "closest_obstacle": "sphere_mid",
            "closest_robot_link": "link_3",
        }), encoding="utf-8")

        manifest_path = tmp_path / "evidence_manifest.json"
        manifest_path.write_text(json.dumps({
            "artifacts": [
                {"kind": "diagnostic_context_json", "exists": True},
                {"kind": "deterministic_report", "exists": True},
                {"kind": "diagnostic_runtime_trace", "exists": True},
                {"kind": "trajectory_overview_data", "exists": True},
            ],
            "evidence_groups": {
                "geometry": {"available": True},
                "safety": {"available": True},
                "diagnostic": {"available": True},
            },
        }), encoding="utf-8")

        report = tmp_path / "diagnostic_report.md"
        report.write_text("# Report", encoding="utf-8")

        output_dir = tmp_path / "analysis_out"

        result = run_diagnostic_analysis(DiagnosticAnalysisRequest(
            context_path=ctx,
            evidence_manifest_path=manifest_path,
            deterministic_report_path=report,
            output_dir=output_dir,
            provider="fake",
        ))

        assert result.analysis_path.exists()
        assert result.provider == "fake"

        loaded = json.loads(result.analysis_path.read_text(encoding="utf-8"))
        assert loaded["schema_version"] == "llm_diagnostic_analysis.v1"
        assert loaded["analysis_mode"] == "fake"
        assert loaded["deterministic_outcome"]["final_status"] == "reject"

    def test_to_app_result_contains_artifact(self, tmp_path):
        ctx = tmp_path / "ctx.json"
        ctx.write_text(json.dumps({"episode_id": "ep2"}), encoding="utf-8")
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps({"evidence_groups": {}}), encoding="utf-8")
        output_dir = tmp_path / "out2"

        result = run_diagnostic_analysis(DiagnosticAnalysisRequest(
            context_path=ctx,
            evidence_manifest_path=manifest_path,
            output_dir=output_dir,
        ))

        app = result.to_app_result()
        assert app.ok is True
        assert app.mode == "diagnostic_analysis"
        assert len(app.artifacts) == 1
        assert app.artifacts[0].kind == "llm_diagnostic_analysis"
        assert app.artifacts[0].path == result.analysis_path

    def test_missing_context_fails(self, tmp_path):
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("{}", encoding="utf-8")

        with pytest.raises(FileNotFoundError):
            run_diagnostic_analysis(DiagnosticAnalysisRequest(
                context_path=tmp_path / "nonexistent.json",
                evidence_manifest_path=manifest_path,
                output_dir=tmp_path / "out",
            ))

    def test_missing_manifest_fails(self, tmp_path):
        ctx = tmp_path / "ctx.json"
        ctx.write_text("{}", encoding="utf-8")

        with pytest.raises(FileNotFoundError):
            run_diagnostic_analysis(DiagnosticAnalysisRequest(
                context_path=ctx,
                evidence_manifest_path=tmp_path / "nonexistent.json",
                output_dir=tmp_path / "out",
            ))

    def test_unsupported_provider_fails(self, tmp_path):
        ctx = tmp_path / "ctx.json"
        ctx.write_text("{}", encoding="utf-8")
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text("{}", encoding="utf-8")

        with pytest.raises(ValueError, match="unsupported.*provider"):
            run_diagnostic_analysis(DiagnosticAnalysisRequest(
                context_path=ctx,
                evidence_manifest_path=manifest_path,
                output_dir=tmp_path / "out",
                provider="deepseek",
            ))
