import json
from pathlib import Path

from robot_safety.evaluator import evaluate_joint_command
from robot_safety.models import JointCommand, Scene

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench/sim_robot_arm"


def _evaluate(task_id: str):
    task_dir = BENCH / task_id
    scene = Scene.from_json(task_dir / "scene.json")
    command = JointCommand.from_json(task_dir / "command.json")
    expected = json.loads((task_dir / "expected.json").read_text(encoding="utf-8"))
    return evaluate_joint_command(scene, command), expected


def test_stage1_benchmark_decisions_match_expected():
    for task_id in (
        "simple_joint_move_001",
        "joint_limit_violation_001",
        "obstacle_collision_001",
        "mid_trajectory_collision_001",
        "near_miss_clearance_001",
        "long_motion_delta_risk_001",
        "multi_obstacle_clearance_001",
    ):
        result, expected = _evaluate(task_id)
        expected_safety = expected["expected_safety"]

        assert result.decision == expected_safety["decision"], task_id
        assert result.risk_level == expected_safety["risk_level"], task_id


def test_obstacle_collision_reports_environment_collision():
    result, expected = _evaluate("obstacle_collision_001")

    assert expected["expected_safety"]["critical_obstacle"] == result.closest_obstacle
    assert "environment_collision" in {item.type for item in result.violations}
    assert result.min_clearance < 0.0


def test_mid_trajectory_collision_reports_nonzero_worst_step():
    result, expected = _evaluate("mid_trajectory_collision_001")

    assert result.decision == "reject"
    assert result.closest_obstacle == expected["expected_safety"]["critical_obstacle"]
    assert result.worst_step is not None
    assert result.worst_step > 0
    assert "environment_collision" in {item.type for item in result.violations}


def test_near_miss_reports_low_clearance_manual_review():
    result, _ = _evaluate("near_miss_clearance_001")

    assert result.decision == "manual_review"
    assert result.trajectory_collision_free
    assert "low_clearance" in {item.type for item in result.violations}


def test_multi_obstacle_reports_closest_information():
    result, expected = _evaluate("multi_obstacle_clearance_001")

    assert result.closest_obstacle == expected["expected_safety"]["critical_obstacle"]
    assert result.closest_robot_link is not None
    assert result.min_clearance > 0.0


def test_safety_result_marks_self_collision_unchecked():
    result, _ = _evaluate("simple_joint_move_001")

    assert result.self_collision_checked is False
    assert result.self_collision_free is None
