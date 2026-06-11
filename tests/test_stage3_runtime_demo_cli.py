import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def _run_demo(task_name: str, tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.run_runtime_demo",
            "--task",
            str(BENCH / task_name),
            "--backend",
            "mock",
            "--episode-dir",
            str(tmp_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_runtime_demo_cli_executes_safe_task(tmp_path):
    payload = _run_demo("simple_joint_move_001", tmp_path)

    assert payload["safety_result"]["decision"] == "approve"
    assert payload["executed"] is True
    assert Path(payload["episode_step_path"]).exists()


def test_runtime_demo_cli_blocks_rejected_task(tmp_path):
    payload = _run_demo("obstacle_collision_001", tmp_path)

    assert payload["safety_result"]["decision"] == "reject"
    assert payload["executed"] is False
    assert payload["blocked_reason"] == "rejected_by_safety_gate"


def test_runtime_demo_cli_blocks_manual_review_task(tmp_path):
    payload = _run_demo("near_miss_clearance_001", tmp_path)

    assert payload["safety_result"]["decision"] == "manual_review"
    assert payload["executed"] is False
    assert payload["blocked_reason"] == "manual_review_required"
