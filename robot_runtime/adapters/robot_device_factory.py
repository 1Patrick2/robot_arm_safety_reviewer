from __future__ import annotations

from .mock_realman_device import MockRealManDevice


def create_robot_device(name: str, *, initial_joints) -> MockRealManDevice:
    normalized = name.strip().lower()
    if normalized == "mock_realman":
        return MockRealManDevice(initial_joints=initial_joints)
    raise ValueError(f"unsupported robot device: {name}")
