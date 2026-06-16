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
        assert payload.get("deterministic_report_path") is not None
        assert Path(payload["deterministic_report_path"]).exists()
        assert payload.get("trace_path") is not None

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
        assert payload.get("agent_report_path") is not None
        assert Path(payload["agent_report_path"]).exists()
        assert payload.get("safety_violations") == []
