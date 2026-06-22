from pathlib import Path

from robot.safety.evaluator import evaluate_joint_command
from robot.safety.models import JointCommand, Scene
from robot.backends.backend_factory import create_backend

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench/sim_robot_arm"


def test_mock_backend_matches_default_evaluator_for_collision_task():
    task_dir = BENCH / "obstacle_collision_001"
    scene = Scene.from_json(task_dir / "scene.json")
    command = JointCommand.from_json(task_dir / "command.json")

    default_result = evaluate_joint_command(scene, command)
    backend_result = evaluate_joint_command(scene, command, backend=create_backend("mock"))

    assert backend_result.to_dict() == default_result.to_dict()


def test_mock_backend_matches_default_evaluator_for_manual_review_task():
    task_dir = BENCH / "near_miss_clearance_001"
    scene = Scene.from_json(task_dir / "scene.json")
    command = JointCommand.from_json(task_dir / "command.json")

    default_result = evaluate_joint_command(scene, command)
    backend_result = evaluate_joint_command(scene, command, backend=create_backend("mock"))

    assert backend_result.to_dict() == default_result.to_dict()
