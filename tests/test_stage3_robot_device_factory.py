import pytest

from robot_runtime.adapters.mock_realman_device import MockRealManDevice
from robot_runtime.adapters.robot_device_factory import create_robot_device


def test_create_robot_device_returns_mock_realman_with_initial_joints():
    device = create_robot_device("mock_realman", initial_joints=(0.1, 0.2, 0, 0, 0, 0))
    device.connect()

    try:
        observation = device.get_observation()
    finally:
        device.disconnect()

    assert isinstance(device, MockRealManDevice)
    assert observation.joint_positions == (0.1, 0.2, 0.0, 0.0, 0.0, 0.0)


def test_create_robot_device_rejects_unknown_device():
    with pytest.raises(ValueError, match="unsupported robot device"):
        create_robot_device("unknown_device", initial_joints=(0, 0, 0, 0, 0, 0))
