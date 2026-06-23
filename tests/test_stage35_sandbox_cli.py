import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "bench" / "samples" / "policy_sequences"
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_sandbox_cli_json(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "sandbox",
            "run",
            "--sequence",
            str(SAMPLES / "simple_safe_sequence.json"),
            "--scene",
            str(BENCH / "simple_joint_move_001" / "scene.json"),
            "--backend",
            "mock",
            "--output-root",
            str(tmp_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["sequence_id"] == "simple_safe_sequence_001"
    assert payload["total_steps"] == 2
    assert payload["approved_steps"] == 2
    assert payload["executed_steps"] == 2
    assert "episode_summary_path" in payload
    assert "clearance_curve_path" in payload
    assert "trajectory_overview_path" in payload
    assert Path(payload["episode_summary_path"]).exists()
    assert Path(payload["clearance_curve_path"]).exists()
    assert Path(payload["trajectory_overview_path"]).exists()


def test_sandbox_cli_text(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "sandbox",
            "run",
            "--sequence",
            str(SAMPLES / "simple_safe_sequence.json"),
            "--scene",
            str(BENCH / "simple_joint_move_001" / "scene.json"),
            "--backend",
            "mock",
            "--output-root",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Sequence: simple_safe_sequence_001" in completed.stdout
    assert "Total Steps: 2" in completed.stdout
    assert "Approved Steps: 2" in completed.stdout
    assert "Episode Summary:" in completed.stdout
    assert "Clearance Curve:" in completed.stdout
    assert "Trajectory Overview:" in completed.stdout
