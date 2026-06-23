import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "bench" / "samples" / "policy_sequences"
BENCH = ROOT / "bench" / "sim_robot_arm"


def _sandbox_episode_dir(tmp_path) -> Path:
    """Run sandbox once and return the episode dir path."""
    from application.sandbox_service import SandboxRunRequest, run_sandbox  # noqa: PLC0415
    result = run_sandbox(
        SandboxRunRequest(
            sequence_path=SAMPLES / "simple_safe_sequence.json",
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            output_root=tmp_path / "sandbox",
        )
    )
    return result.sequence_runtime_result.episode_dir


class TestMetricsCliIngest:
    def test_ingest_json(self, tmp_path):
        ep_dir = _sandbox_episode_dir(tmp_path)
        db_path = tmp_path / "metrics.db"

        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "metrics", "ingest",
                "--episode-dir", str(ep_dir),
                "--db", str(db_path),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload.get("total_steps") == 2
        assert payload.get("approved_steps") == 2

    def test_ingest_text(self, tmp_path):
        ep_dir = _sandbox_episode_dir(tmp_path)
        db_path = tmp_path / "metrics.db"

        completed = subprocess.run(
            [
                sys.executable,
                "-m", "cli.main",
                "metrics", "ingest",
                "--episode-dir", str(ep_dir),
                "--db", str(db_path),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        assert "Total Steps: 2" in completed.stdout
        assert "Approved Steps: 2" in completed.stdout


class TestMetricsCliListRuns:
    def test_list_runs_json(self, tmp_path):
        db_path = tmp_path / "metrics.db"
        ep_dir = _sandbox_episode_dir(tmp_path)

        # ingest first
        subprocess.run(
            [sys.executable, "-m", "cli.main", "metrics", "ingest",
             "--episode-dir", str(ep_dir), "--db", str(db_path)],
            cwd=ROOT, check=True, capture_output=True,
        )

        completed = subprocess.run(
            [sys.executable, "-m", "cli.main", "metrics", "list-runs",
             "--db", str(db_path), "--json"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload["count"] >= 1


class TestMetricsCliShowRun:
    def test_show_run_json(self, tmp_path):
        db_path = tmp_path / "metrics.db"
        ep_dir = _sandbox_episode_dir(tmp_path)

        # ingest first
        subprocess.run(
            [sys.executable, "-m", "cli.main", "metrics", "ingest",
             "--episode-dir", str(ep_dir), "--db", str(db_path)],
            cwd=ROOT, check=True, capture_output=True,
        )

        completed = subprocess.run(
            [sys.executable, "-m", "cli.main", "metrics", "show-run",
             "--db", str(db_path), "--episode-id", ep_dir.name, "--json"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )

        payload = json.loads(completed.stdout)
        assert payload["run"] is not None
        assert payload["step_count"] == 2
