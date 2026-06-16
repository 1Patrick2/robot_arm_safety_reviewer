import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples" / "policy_sequences"
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

        case = payload["cases"][0]
        assert case["case_id"] == "simple_safe_sequence"
        assert case["ok"] is True
        assert case["episode_id"] is not None
        assert case["context_path"] is not None
        assert Path(case["context_path"]).exists()
        assert case["deterministic_report_path"] is not None
        assert Path(case["deterministic_report_path"]).exists()
        assert case["trace_path"] is not None
        assert Path(case["trace_path"]).exists()
        assert case["evidence_manifest_path"] is not None
        assert Path(case["evidence_manifest_path"]).exists()
