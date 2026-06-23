import json
import subprocess
import sys
from pathlib import Path

from application.gateway.safety_gate import execute_if_safe, review_only

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench/sim_robot_arm"


def test_review_only_writes_replayable_log(tmp_path):
    task_dir = BENCH / "obstacle_collision_001"

    outcome = review_only(task_dir / "scene.json", task_dir / "command.json", log_dir=tmp_path)

    assert outcome.safety_result.decision == "reject"
    assert outcome.log_path is not None
    payload = json.loads(outcome.log_path.read_text(encoding="utf-8"))
    assert payload["scene_id"] == "obstacle_collision_001"
    assert payload["schema_version"] == "stage1.execution_log.v1"
    assert payload["mode"] == "review_only"
    assert payload["input_paths"]["scene_path"]
    assert payload["review_summary"]["decision"] == "reject"
    assert payload["trajectory_summary"]["collision_free"] is False
    assert payload["environment"]["backend"] == "mock"
    assert payload["command_id"] == "cmd_obstacle_collision_001"
    assert payload["safety_result"]["decision"] == "reject"
    assert payload["execution"]["executed"] is False
    assert payload["execution"]["reason"] == "review_only"


def test_execute_if_safe_simulates_only_approved_commands(tmp_path):
    safe_dir = BENCH / "simple_joint_move_001"
    unsafe_dir = BENCH / "obstacle_collision_001"

    safe = execute_if_safe(safe_dir / "scene.json", safe_dir / "command.json", log_dir=tmp_path)
    unsafe = execute_if_safe(unsafe_dir / "scene.json", unsafe_dir / "command.json", log_dir=tmp_path)

    assert safe.execution_log["execution"]["executed"] is True
    assert safe.execution_log["execution"]["reason"] == "mock_execution_complete"
    assert safe.execution_log["execution"]["adapter_result"]["executed"] is True
    assert unsafe.execution_log["execution"]["executed"] is False
    assert unsafe.execution_log["execution"]["reason"] == "rejected_by_safety_gate"


def test_review_command_cli_outputs_summary_and_log(tmp_path):
    task_dir = BENCH / "obstacle_collision_001"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.review_command",
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

    assert "Decision: reject" in completed.stdout
    assert "Risk Level: high" in completed.stdout
    assert "Violations:" in completed.stdout
    assert "Evidence:" in completed.stdout
    assert list(tmp_path.glob("exec_*.json"))


def test_review_command_cli_json_output(tmp_path):
    task_dir = BENCH / "obstacle_collision_001"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.review_command",
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
    assert payload["risk_level"] == "high"
    assert payload["violations"][0]["type"] == "environment_collision"


def test_review_only_turns_invalid_command_into_reject_log(tmp_path):
    task_dir = BENCH / "invalid_command_001"

    outcome = review_only(task_dir / "scene.json", task_dir / "command.json", log_dir=tmp_path)

    assert outcome.safety_result.decision == "reject"
    assert outcome.safety_result.risk_level == "high"
    assert outcome.safety_result.violations[0].type == "invalid_command"
    assert outcome.execution_log["execution"]["executed"] is False


def test_execute_if_safe_logs_adapter_failure(tmp_path):
    class FailingAdapter:
        robot_id = "failing_robot"

        def get_joint_state(self):
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        def execute_joint_move(self, target_joints, speed):
            raise RuntimeError("adapter offline")

        def stop(self):
            return None

    task_dir = BENCH / "simple_joint_move_001"

    outcome = execute_if_safe(
        task_dir / "scene.json",
        task_dir / "command.json",
        robot_adapter=FailingAdapter(),
        log_dir=tmp_path,
    )

    assert outcome.safety_result.decision == "approve"
    assert outcome.execution_log["execution"]["executed"] is False
    assert outcome.execution_log["execution"]["reason"] == "adapter_execution_failed"
    assert outcome.execution_log["execution"]["adapter_result"]["error_message"] == "adapter offline"
