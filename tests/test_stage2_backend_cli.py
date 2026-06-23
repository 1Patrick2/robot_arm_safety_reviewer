import json
import subprocess
import sys
from pathlib import Path

import pytest

from application.gateway.safety_gate import review_only

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench/sim_robot_arm"


def test_review_only_records_backend_metadata(tmp_path):
    task_dir = BENCH / "obstacle_collision_001"

    outcome = review_only(
        task_dir / "scene.json",
        task_dir / "command.json",
        backend_name="mock",
        log_dir=tmp_path,
    )

    assert outcome.execution_log["review_backend"]["name"] == "mock"
    assert outcome.execution_log["environment"]["backend"] == "mock"
    assert outcome.safety_result.decision == "reject"


def test_review_command_cli_accepts_mock_backend(tmp_path):
    task_dir = BENCH / "obstacle_collision_001"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.review_command",
            "--backend",
            "mock",
            "--scene",
            str(task_dir / "scene.json"),
            "--command",
            str(task_dir / "command.json"),
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
    assert payload["decision"] == "reject"


def test_run_benchmark_cli_accepts_mock_backend(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.run_benchmark",
            "--backend",
            "mock",
            "--bench",
            str(BENCH),
            "--log-dir",
            str(tmp_path / "logs"),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["total"] == 8
    assert payload["failed"] == 0


def test_review_command_cli_accepts_pybullet_backend(tmp_path):
    pytest.importorskip("pybullet")
    task_dir = BENCH / "simple_joint_move_001"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.review_command",
            "--backend",
            "pybullet",
            "--scene",
            str(task_dir / "scene.json"),
            "--command",
            str(task_dir / "command.json"),
            "--log-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "Decision:" in completed.stdout
