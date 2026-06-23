import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "bench" / "samples" / "policy_sequences"
BENCH = ROOT / "bench" / "sim_robot_arm"


def _sandbox_and_ingest(tmp_path) -> tuple[Path, str]:
    from application.sandbox_service import SandboxRunRequest, run_sandbox  # noqa: PLC0415

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
    ep_id = result.sequence_runtime_result.episode_dir.name
    return db_path, ep_id


class TestContextCliBuild:
    def test_build_json(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        out_dir = tmp_path / "context_output"

        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "context", "build",
                "--db", str(db_path),
                "--episode-id", ep_id,
                "--output-dir", str(out_dir),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload["episode_id"] == ep_id
        assert payload["critical_step_count"] >= 0
        assert payload["json_path"] is not None
        assert payload["markdown_path"] is not None
        assert Path(payload["json_path"]).exists()
        assert Path(payload["markdown_path"]).exists()

    def test_build_text(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)

        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "context", "build",
                "--db", str(db_path),
                "--episode-id", ep_id,
                "--output-dir", str(tmp_path / "ctx_out"),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        assert f"Episode ID: {ep_id}" in completed.stdout
        assert "Total Steps: 2" in completed.stdout
        assert "Critical Steps:" in completed.stdout
