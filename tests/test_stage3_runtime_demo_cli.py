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


def _result(payload):
    return payload["result"]


def test_runtime_demo_cli_executes_safe_task(tmp_path):
    payload = _run_demo("simple_joint_move_001", tmp_path)
    result = _result(payload)

    assert payload["task"].endswith("simple_joint_move_001")
    assert payload["backend"] == "mock"
    assert Path(payload["episode_dir"]).exists()
    assert result["safety_result"]["decision"] == "approve"
    assert result["executed"] is True
    assert result["execution_result"]["success"] is True
    assert Path(result["episode_step_path"]).exists()


def test_runtime_demo_cli_blocks_rejected_task(tmp_path):
    payload = _run_demo("obstacle_collision_001", tmp_path)
    result = _result(payload)

    assert result["safety_result"]["decision"] == "reject"
    assert result["executed"] is False
    assert result["execution_result"] is None
    assert result["blocked_reason"] == "rejected_by_safety_gate"


def test_runtime_demo_cli_blocks_manual_review_task(tmp_path):
    payload = _run_demo("near_miss_clearance_001", tmp_path)
    result = _result(payload)

    assert result["safety_result"]["decision"] == "manual_review"
    assert result["executed"] is False
    assert result["execution_result"] is None
    assert result["blocked_reason"] == "manual_review_required"


def test_runtime_demo_cli_fails_when_task_files_are_missing(tmp_path):
    task_dir = tmp_path / "missing_task"
    task_dir.mkdir()

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.run_runtime_demo",
            "--task",
            str(task_dir),
            "--backend",
            "mock",
            "--episode-dir",
            str(tmp_path / "episode"),
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "scene.json not found" in completed.stderr
