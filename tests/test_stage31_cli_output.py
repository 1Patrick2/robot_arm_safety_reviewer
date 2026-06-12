import json
from pathlib import Path

from application.review_service import ReviewCommandRequest, review_command
from application.runtime_service import RuntimeTaskRequest, run_runtime_task
from cli.output import print_review_command_result, print_runtime_task_result


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_print_runtime_task_result_text_preserves_existing_fields(tmp_path, capsys):
    result = run_runtime_task(
        RuntimeTaskRequest(
            task_dir=BENCH / "simple_joint_move_001",
            backend_name="mock",
            episode_root=tmp_path,
        )
    )

    print_runtime_task_result(result, as_json=False)

    safety = result.step_result.safety_result
    output = capsys.readouterr().out
    assert f"Decision: {safety.decision}" in output
    assert f"Risk Level: {safety.risk_level}" in output
    assert "Executed: True" in output
    assert "Blocked Reason: None" in output
    assert f"Episode Dir: {result.episode_dir}" in output
    assert f"Episode Step Path: {result.step_result.episode_step_path}" in output


def test_print_runtime_task_result_json_uses_result_payload(tmp_path, capsys):
    result = run_runtime_task(
        RuntimeTaskRequest(
            task_dir=BENCH / "simple_joint_move_001",
            backend_name="mock",
            episode_root=tmp_path,
        )
    )

    print_runtime_task_result(result, as_json=True)

    payload = json.loads(capsys.readouterr().out)
    assert payload == result.to_dict()


def test_print_review_command_result_text_preserves_existing_fields(tmp_path, capsys):
    task_dir = BENCH / "obstacle_collision_001"
    result = review_command(
        ReviewCommandRequest(
            scene_path=task_dir / "scene.json",
            command_path=task_dir / "command.json",
            backend_name="mock",
            log_dir=tmp_path,
        )
    )

    print_review_command_result(result, as_json=False)

    safety = result.safety_result
    output = capsys.readouterr().out
    assert f"Decision: {safety.decision}" in output
    assert f"Risk Level: {safety.risk_level}" in output
    assert f"Min Clearance: {safety.min_clearance}" in output
    assert f"Closest Link: {safety.closest_robot_link}" in output
    assert f"Closest Obstacle: {safety.closest_obstacle}" in output
    assert f"Worst Step: {safety.worst_step}" in output
    assert f"Log Path: {result.log_path}" in output


def test_print_review_command_result_json_uses_result_payload(tmp_path, capsys):
    task_dir = BENCH / "obstacle_collision_001"
    result = review_command(
        ReviewCommandRequest(
            scene_path=task_dir / "scene.json",
            command_path=task_dir / "command.json",
            backend_name="mock",
            log_dir=tmp_path,
        )
    )

    print_review_command_result(result, as_json=True)

    payload = json.loads(capsys.readouterr().out)
    assert payload == result.to_dict()
