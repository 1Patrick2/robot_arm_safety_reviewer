import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "bench" / "samples" / "policy_sequences"
BENCH = ROOT / "bench" / "sim_robot_arm"


def _sandbox_and_ingest(tmp_path) -> tuple[Path, str]:
    """Run sandbox with metrics-db and return (db_path, episode_id)."""
    from application.sandbox_service import SandboxRunRequest, run_sandbox
    db_path = tmp_path / "metrics.db"
    result = run_sandbox(
        SandboxRunRequest(
            sequence_path=SAMPLES / "simple_safe_sequence.json",
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            output_root=tmp_path / "sandbox",
            metrics_db=db_path,
        )
    )
    return db_path, result.sequence_runtime_result.episode_dir.name


class TestDiagnosticCli:
    def test_diagnostic_run_json(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        output_dir = tmp_path / "diagnostic_out"

        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "diagnostic", "run",
                "--episode-id", ep_id,
                "--db", str(db_path),
                "--output-dir", str(output_dir),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload.get("episode_id") == ep_id
        assert payload.get("total_steps") == 2
        assert payload.get("context_path") is not None
        assert Path(payload["context_path"]).exists()
        assert payload.get("deterministic_report_path") is not None
        assert Path(payload["deterministic_report_path"]).exists()
        assert payload.get("trace_path") is not None

        # Output is under episode sub-directory
        ep_dir = output_dir / ep_id
        assert ep_dir.exists()

        # Evidence manifest
        assert payload.get("evidence_manifest_path") is not None
        manifest_path = Path(payload["evidence_manifest_path"])
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["episode_id"] == ep_id
        assert manifest["checks"]["has_diagnostic_context"] is True
        assert manifest["checks"]["has_diagnostic_report"] is True
        assert manifest["checks"]["has_trace"] is True

    def test_diagnostic_run_with_agent(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        output_dir = tmp_path / "diag_agent"

        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "diagnostic", "run",
                "--episode-id", ep_id,
                "--db", str(db_path),
                "--output-dir", str(output_dir),
                "--run-agent",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload.get("episode_id") == ep_id
        assert payload.get("context_path") is not None
        assert payload.get("agent_report_path") is not None
        assert Path(payload["agent_report_path"]).exists()
        assert payload.get("safety_violations") == []

        # Evidence manifest: agent report included
        assert payload.get("evidence_manifest_path") is not None
        manifest_path = Path(payload["evidence_manifest_path"])
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["checks"]["has_agent_report"] is True
        manifest_kinds = {a["kind"] for a in manifest["artifacts"]}
        assert "diagnostic_agent_report" in manifest_kinds

    def test_diagnostic_report_json(self, tmp_path):
        """diagnostic report should generate report + trace from existing context, no agent."""
        # First build a context via the run path
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        run_out = tmp_path / "run_out"
        run_completed = subprocess.run(
            [sys.executable, "-m", "cli.main", "diagnostic", "run",
             "--episode-id", ep_id, "--db", str(db_path),
             "--output-dir", str(run_out), "--json"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        run_payload = json.loads(run_completed.stdout)
        context_path = run_payload["context_path"]

        # Now call diagnostic report on that context
        report_out = tmp_path / "report_out"
        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "diagnostic", "report",
                "--context", context_path,
                "--output-dir", str(report_out),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        assert "context_path" in payload
        assert payload.get("deterministic_report_path") is not None
        assert Path(payload["deterministic_report_path"]).exists()
        assert payload.get("trace_path") is not None
        # No agent report for report-only command
        assert "agent_report_path" not in payload or payload["agent_report_path"] is None

        # Evidence manifest: report and trace present, no agent
        assert payload.get("evidence_manifest_path") is not None
        manifest_path = Path(payload["evidence_manifest_path"])
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["checks"]["has_diagnostic_report"] is True
        assert manifest["checks"]["has_trace"] is True
        assert manifest["checks"]["has_agent_report"] is False


class TestDiagnosticRegression:
    def test_diagnostic_regression_json(self, tmp_path):
        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "diagnostic", "regression",
                "--output-dir", str(tmp_path / "regression"),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload["schema_version"] == "diagnostic_regression.v1"
        assert payload["total_cases"] >= 1
        assert payload["passed_cases"] >= 1
        assert payload["failed_cases"] == 0
        assert payload["summary_path"] is not None
        assert Path(payload["summary_path"]).exists()

        # Summary file content matches CLI output
        summary = json.loads(Path(payload["summary_path"]).read_text(encoding="utf-8"))
        assert summary["schema_version"] == payload["schema_version"]
        assert summary["total_cases"] == payload["total_cases"]
        assert summary["summary_path"] == payload["summary_path"]

        case = payload["cases"][0]
        assert case["case_id"] == "simple_safe_sequence"
        assert case["ok"] is True
        assert case["errors"] == []
        assert case["pipeline_passed"] is True
        assert case["evidence_complete"] is True
        assert case["contract_passed"] is None
        assert case["expected"] is None
        assert case["actual"] is not None
        assert case["episode_id"] is not None
        assert case["context_path"] is not None
        assert Path(case["context_path"]).exists()
        assert case["deterministic_report_path"] is not None
        assert Path(case["deterministic_report_path"]).exists()
        assert case["trace_path"] is not None
        assert Path(case["trace_path"]).exists()
        assert case["evidence_manifest_path"] is not None
        assert Path(case["evidence_manifest_path"]).exists()

        # Evidence manifest indexes trajectory_overview_data
        manifest = json.loads(Path(case["evidence_manifest_path"]).read_text(encoding="utf-8"))
        manifest_kinds = {a["kind"] for a in manifest["artifacts"]}
        assert "trajectory_overview_data" in manifest_kinds
        assert manifest["checks"]["has_structured_visual_data"] is True

    def test_diagnostic_regression_with_agent_json(self, tmp_path):
        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "diagnostic", "regression",
                "--output-dir", str(tmp_path / "regression_agent"),
                "--run-agent",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload["schema_version"] == "diagnostic_regression.v1"
        assert payload["total_cases"] >= 1
        assert payload["passed_cases"] >= 1
        assert payload["failed_cases"] == 0

        case = payload["cases"][0]
        assert case["ok"] is True
        assert case["errors"] == []
        assert case["pipeline_passed"] is True
        assert case["evidence_complete"] is True
        assert case["contract_passed"] is None
        assert case["agent_report_path"] is not None
        assert Path(case["agent_report_path"]).exists()
        assert case["evidence_manifest_path"] is not None
        assert Path(case["evidence_manifest_path"]).exists()

        manifest = json.loads(Path(case["evidence_manifest_path"]).read_text(encoding="utf-8"))
        assert manifest["checks"]["has_agent_report"] is True

    def test_diagnostic_regression_with_expected_contract(self, tmp_path):
        """Regression with an expected contract should produce pipeline/evidence/contract fields."""
        from application.diagnostic_service import (
            DiagnosticRegressionCase,
            DiagnosticRegressionRequest,
            run_diagnostic_regression,
        )

        # Create a temporary expected_contract.json for the simple_safe_sequence
        contract_dir = tmp_path / "contracts"
        contract_dir.mkdir(parents=True, exist_ok=True)
        contract_path = contract_dir / "simple_safe_expected.json"
        contract_path.write_text(json.dumps({
            "schema_version": "expected_contract.v1",
            "case_id": "simple_safe_sequence",
            "expected": {
                "total_steps": 2,
                "min_approved_steps": 2,
                "min_manual_review_steps": 0,
                "min_rejected_steps": 0,
                "expected_final_status": "approve",
                "required_artifacts": [
                    "diagnostic_context_json",
                    "deterministic_report",
                    "diagnostic_runtime_trace",
                    "evidence_manifest",
                ],
            },
        }), encoding="utf-8")

        result = run_diagnostic_regression(
            DiagnosticRegressionRequest(
                cases=(
                    DiagnosticRegressionCase(
                        case_id="simple_safe_sequence",
                        sequence_path=SAMPLES / "simple_safe_sequence.json",
                        scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                        expected_contract_path=contract_path,
                    ),
                ),
                output_dir=tmp_path / "regression_contract",
            )
        )

        assert result.total_cases == 1
        assert result.passed_cases == 1
        assert result.failed_cases == 0

        case = result.case_results[0]
        assert case.ok is True
        assert case.pipeline_passed is True
        assert case.evidence_complete is True
        assert case.contract_passed is True
        assert case.expected is not None
        assert case.expected["expected_final_status"] == "approve"
        assert case.actual is not None
        assert case.actual["final_status"] == "approve"
        assert case.actual["total_steps"] == 2
        assert case.errors == ()

    def test_diagnostic_regression_contract_case_id_mismatch(self, tmp_path):
        """When contract case_id differs from the regression case, the case must fail."""
        from application.diagnostic_service import (
            DiagnosticRegressionCase,
            DiagnosticRegressionRequest,
            run_diagnostic_regression,
        )

        contract_dir = tmp_path / "contracts"
        contract_dir.mkdir(parents=True, exist_ok=True)
        contract_path = contract_dir / "mismatched.json"
        contract_path.write_text(json.dumps({
            "schema_version": "expected_contract.v1",
            "case_id": "different_case",
            "expected": {
                "total_steps": 2,
                "min_approved_steps": 2,
                "expected_final_status": "approve",
            },
        }), encoding="utf-8")

        result = run_diagnostic_regression(
            DiagnosticRegressionRequest(
                cases=(
                    DiagnosticRegressionCase(
                        case_id="simple_safe_sequence",
                        sequence_path=SAMPLES / "simple_safe_sequence.json",
                        scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                        expected_contract_path=contract_path,
                    ),
                ),
                output_dir=tmp_path / "regression_mismatch",
            )
        )

        case = result.case_results[0]
        assert case.ok is False
        assert case.contract_passed is False
        assert any("case_id mismatch" in e for e in case.errors)

    def test_diagnostic_regression_case_set_level2_json(self, tmp_path):
        """--case-set level2 runs 3 Level-2 cases, all contract_passed."""
        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "diagnostic", "regression",
                "--case-set", "level2",
                "--output-dir", str(tmp_path / "reg_level2"),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload["schema_version"] == "diagnostic_regression.v1"
        assert payload["total_cases"] == 3
        assert payload["passed_cases"] == 3
        assert payload["failed_cases"] == 0

        case_ids = {c["case_id"] for c in payload["cases"]}
        assert case_ids == {
            "near_threshold_clearance_sequence",
            "midpoint_collision_sequence",
            "mixed_decision_sequence",
        }

        for case in payload["cases"]:
            assert case["ok"] is True
            assert case["pipeline_passed"] is True
            assert case["evidence_complete"] is True
            assert case["contract_passed"] is True
            assert case["expected"] is not None
            assert "required_evidence_groups" in case["expected"]
            assert "required_actual_fields" in case["expected"]
            assert "expected_closest_obstacle" in case["expected"]
            assert "min_clearance_lte" in case["expected"]
            assert case["actual"] is not None
            assert case["actual"].get("closest_obstacle") == case["expected"]["expected_closest_obstacle"]
            assert case["errors"] == []
            assert case["evidence_manifest_path"] is not None
            assert Path(case["evidence_manifest_path"]).exists()

    def test_diagnostic_regression_case_set_all_json(self, tmp_path):
        """--case-set all runs smoke + level2 (4 cases), all pass."""
        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "diagnostic", "regression",
                "--case-set", "all",
                "--output-dir", str(tmp_path / "reg_all"),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload["schema_version"] == "diagnostic_regression.v1"
        assert payload["total_cases"] == 4
        assert payload["passed_cases"] == 4
        assert payload["failed_cases"] == 0

        case_ids = {c["case_id"] for c in payload["cases"]}
        assert case_ids == {
            "simple_safe_sequence",
            "near_threshold_clearance_sequence",
            "midpoint_collision_sequence",
            "mixed_decision_sequence",
        }

        for case in payload["cases"]:
            assert case["ok"] is True
            assert case["pipeline_passed"] is True
            assert case["evidence_complete"] is True
            assert case["errors"] == []

            if case["case_id"] == "simple_safe_sequence":
                assert case["contract_passed"] is None
                assert case["expected"] is None
            else:
                assert case["contract_passed"] is True
                assert case["expected"] is not None

            assert case["actual"] is not None

    def test_diagnostic_analyze_json(self, tmp_path):
        """diagnostic analyze produces llm_diagnostic_analysis.json."""
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_cli",
            "sequence_id": "cli_test",
            "total_steps": 2,
            "approved_steps": 2,
            "manual_review_steps": 0,
            "rejected_steps": 0,
            "min_clearance": 0.15,
        }), encoding="utf-8")

        manifest_path = tmp_path / "evidence_manifest.json"
        manifest_path.write_text(json.dumps({
            "artifacts": [{"kind": "diagnostic_context_json", "exists": True}],
            "evidence_groups": {},
        }), encoding="utf-8")

        output_dir = tmp_path / "cli_analysis"
        completed = subprocess.run(
            [
                sys.executable, "-m", "cli.main",
                "diagnostic", "analyze",
                "--context", str(ctx),
                "--manifest", str(manifest_path),
                "--output-dir", str(output_dir),
                "--provider", "fake",
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload["ok"] is True
        assert payload["mode"] == "diagnostic_analysis"
        assert payload["data"]["schema_version"] == "diagnostic_analysis_result.v1"
        assert Path(payload["data"]["analysis_path"]).exists()

        analysis = json.loads(Path(payload["data"]["analysis_path"]).read_text(encoding="utf-8"))
        assert analysis["schema_version"] == "llm_diagnostic_analysis.v1"
        assert analysis["analysis_mode"] == "fake"
