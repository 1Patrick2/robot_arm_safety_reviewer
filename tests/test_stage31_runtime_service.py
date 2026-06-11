from pathlib import Path

import pytest

from application.runtime_service import RuntimeTaskRequest, run_runtime_task


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_run_runtime_task_executes_safe_task(tmp_path):
    result = run_runtime_task(
        RuntimeTaskRequest(
            task_dir=BENCH / "simple_joint_move_001",
            backend_name="mock",
            episode_root=tmp_path,
        )
    )

    payload = result.to_dict()

    assert payload["task"].endswith("simple_joint_move_001")
    assert payload["backend"] == "mock"
    assert payload["result"]["safety_result"]["decision"] == "approve"
    assert payload["result"]["executed"] is True
    assert payload["result"]["execution_result"]["success"] is True
    assert result.episode_dir.exists()


def test_run_runtime_task_blocks_manual_review_task(tmp_path):
    result = run_runtime_task(
        RuntimeTaskRequest(
            task_dir=BENCH / "near_miss_clearance_001",
            backend_name="mock",
            episode_root=tmp_path,
        )
    )

    step = result.step_result

    assert step.safety_result.decision == "manual_review"
    assert step.executed is False
    assert step.sent_action is None
    assert step.execution_result is None
    assert step.blocked_reason == "manual_review_required"


def test_run_runtime_task_rejects_missing_task_files(tmp_path):
    task_dir = tmp_path / "missing_task"
    task_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="scene.json not found"):
        run_runtime_task(RuntimeTaskRequest(task_dir=task_dir, episode_root=tmp_path / "episode"))
