from robot.runtime.action_sequence import PolicyActionSequence
from robot.runtime.adapters.mock_realman_device import MockRealManDevice
from robot.runtime.adapters.robot_device_factory import create_robot_device
from robot.runtime.policy_action import PolicyAction
from robot.runtime.safety_runtime import SafetyRuntime
from robot.runtime.types import RobotAction, RobotObservation
from robot_runtime.action_sequence import PolicyActionSequence as LegacyPolicyActionSequence
from robot_runtime.adapters.mock_realman_device import MockRealManDevice as LegacyMockRealManDevice
from robot_runtime.adapters.robot_device_factory import create_robot_device as legacy_create_robot_device
from robot_runtime.policy_action import PolicyAction as LegacyPolicyAction
from robot_runtime.safety_runtime import SafetyRuntime as LegacySafetyRuntime
from robot_runtime.types import RobotAction as LegacyRobotAction
from robot_runtime.types import RobotObservation as LegacyRobotObservation


def test_robot_runtime_new_package_path_matches_legacy_path():
    assert PolicyActionSequence is LegacyPolicyActionSequence
    assert MockRealManDevice is LegacyMockRealManDevice
    assert create_robot_device is legacy_create_robot_device
    assert PolicyAction is LegacyPolicyAction
    assert SafetyRuntime is LegacySafetyRuntime
    assert RobotAction is LegacyRobotAction
    assert RobotObservation is LegacyRobotObservation
