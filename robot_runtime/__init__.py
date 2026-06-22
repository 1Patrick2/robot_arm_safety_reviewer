"""Compatibility package for robot runtime primitives.

New code should import from ``robot.runtime``. This package remains as a
temporary shim while existing imports migrate.
"""

from robot.runtime import PolicyAction, PolicyActionSequence, RobotAction, RobotObservation, RuntimeStepResult, policy_action_to_robot_action

__all__ = [
    "PolicyAction",
    "PolicyActionSequence",
    "RobotAction",
    "RobotObservation",
    "RuntimeStepResult",
    "policy_action_to_robot_action",
]
