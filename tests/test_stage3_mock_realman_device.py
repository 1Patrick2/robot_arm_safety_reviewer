import pytest

from robot_runtime.adapters.mock_realman_device import MockRealManDevice
from robot_runtime.types import RobotAction


def test_mock_realman_device_connect_enables_observation():
    device = MockRealManDevice(initial_joints=(0.0,) * 6)

    assert device.is_connected is False
    device.connect()
    observation = device.get_observation()

    assert device.is_connected is True
    assert observation.robot_id == "mock_realman_6dof"
    assert observation.joint_positions == (0.0,) * 6
    assert "timestamp" in observation.to_dict()


def test_mock_realman_device_send_action_requires_connection():
    device = MockRealManDevice(initial_joints=(0.0,) * 6)
    action = RobotAction(action_type="joint_move", target_joints=(0.1,) * 6)

    with pytest.raises(ConnectionError, match="not connected"):
        device.send_action(action)


def test_mock_realman_device_send_action_updates_joint_state():
    device = MockRealManDevice(initial_joints=(0.0,) * 6)
    device.connect()
    action = RobotAction(action_type="joint_move", target_joints=(0.1, 0.2, 0.0, 0.0, 0.0, 0.0), speed=0.2)

    execution_result = device.send_action(action)

    assert execution_result.attempted is True
    assert execution_result.success is True
    assert execution_result.reason == "executed"
    assert execution_result.simulated is True
    assert execution_result.metadata["execution_count"] == 1
    assert device.get_observation().joint_positions == action.target_joints
    assert device.execution_count == 1


def test_mock_realman_device_disconnect_blocks_observation_and_action():
    device = MockRealManDevice(initial_joints=(0.0,) * 6)
    device.connect()
    device.disconnect()

    with pytest.raises(ConnectionError, match="not connected"):
        device.get_observation()

    with pytest.raises(ConnectionError, match="not connected"):
        device.send_action(RobotAction(action_type="joint_move", target_joints=(0.1,) * 6))
