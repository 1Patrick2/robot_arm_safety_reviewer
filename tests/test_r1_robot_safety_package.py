from robot.safety.evaluator import evaluate_joint_command
from robot.safety.models import JointCommand, Scene
from robot.safety.evaluator import evaluate_joint_command as legacy_evaluate_joint_command
from robot.safety.models import JointCommand as LegacyJointCommand
from robot.safety.models import Scene as LegacyScene


def test_robot_safety_new_package_path_matches_legacy_path():
    assert Scene is LegacyScene
    assert JointCommand is LegacyJointCommand
    assert evaluate_joint_command is legacy_evaluate_joint_command
