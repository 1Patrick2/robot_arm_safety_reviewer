import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_unified_cli_runtime_run_invokes_runtime_service(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "runtime",
            "run",
            "--task",
            str(BENCH / "simple_joint_move_001"),
            "--backend",
            "mock",
            "--episode-root",
            str(tmp_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["backend"] == "mock"
    assert payload["result"]["safety_result"]["decision"] == "approve"
    assert payload["result"]["executed"] is True


def test_unified_cli_review_invokes_review_service(tmp_path):
    task_dir = BENCH / "obstacle_collision_001"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "review",
            "--scene",
            str(task_dir / "scene.json"),
            "--command",
            str(task_dir / "command.json"),
            "--backend",
            "mock",
            "--log-dir",
            str(tmp_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["safety_result"]["decision"] == "reject"
    assert payload["backend"] == "mock"
    assert Path(payload["log_path"]).exists()
