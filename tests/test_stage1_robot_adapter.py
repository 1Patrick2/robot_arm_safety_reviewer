import json
import subprocess
import sys
from pathlib import Path

import pytest

from robot.adapters.mock_realman_6dof import MockRealMan6DoFAdapter

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench/sim_robot_arm"


def test_mock_realman_adapter_executes_joint_move_in_memory():
    adapter = MockRealMan6DoFAdapter(initial_joints=[0.0] * 6)

    result = adapter.execute_joint_move((0.1, 0.2, 0.3, 0.0, -0.1, 0.0), speed=0.2)

    assert result.executed
    assert result.success
    assert result.reason == "mock_execution_complete"
    assert result.start_joints == pytest.approx((0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    assert result.target_joints == pytest.approx((0.1, 0.2, 0.3, 0.0, -0.1, 0.0))
    assert result.speed == pytest.approx(0.2)
    assert result.simulated is True
    assert result.execution_count == 1
    assert adapter.get_joint_state() == pytest.approx((0.1, 0.2, 0.3, 0.0, -0.1, 0.0))
    assert adapter.last_target_joints == pytest.approx((0.1, 0.2, 0.3, 0.0, -0.1, 0.0))
    assert adapter.execution_count == 1


def test_mock_realman_adapter_rejects_bad_dimensions():
    adapter = MockRealMan6DoFAdapter()

    with pytest.raises(ValueError, match="six values"):
        adapter.execute_joint_move((0.1, 0.2), speed=0.2)


def test_execute_if_safe_cli_executes_safe_command(tmp_path):
    task_dir = BENCH / "simple_joint_move_001"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.execute_if_safe",
            "--scene",
            str(task_dir / "scene.json"),
            "--command",
            str(task_dir / "command.json"),
            "--log-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Decision: approve" in completed.stdout
    assert "Executed: True" in completed.stdout
    assert "Execution Reason: mock_execution_complete" in completed.stdout
    assert "Evidence:" in completed.stdout


def test_execute_if_safe_cli_json_output(tmp_path):
    task_dir = BENCH / "simple_joint_move_001"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.execute_if_safe",
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
    assert payload["safety_result"]["decision"] == "approve"
    assert payload["execution"]["executed"] is True
    assert payload["execution"]["reason"] == "mock_execution_complete"
