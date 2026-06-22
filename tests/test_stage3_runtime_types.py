from robot.runtime.types import RobotAction, RobotObservation


def test_robot_observation_serializes_to_dict():
    observation = RobotObservation(
        robot_id="mock_realman_6dof",
        joint_positions=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5),
        timestamp="2026-06-11T10:00:00Z",
        metadata={"source": "test"},
    )

    assert observation.to_dict() == {
        "robot_id": "mock_realman_6dof",
        "joint_positions": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
        "timestamp": "2026-06-11T10:00:00Z",
        "metadata": {"source": "test"},
    }


def test_robot_action_serializes_to_dict():
    action = RobotAction(
        action_type="joint_move",
        target_joints=(0.1, 0.2, 0.0, 0.0, 0.0, 0.0),
        speed=0.2,
        source="replay",
        metadata={"command_id": "cmd_simple_joint_move_001"},
    )

    assert action.to_dict() == {
        "action_type": "joint_move",
        "target_joints": [0.1, 0.2, 0.0, 0.0, 0.0, 0.0],
        "speed": 0.2,
        "source": "replay",
        "metadata": {"command_id": "cmd_simple_joint_move_001"},
    }


def test_robot_action_rejects_non_joint_move():
    try:
        RobotAction(action_type="cartesian_move", target_joints=(0.0,) * 6)
    except ValueError as exc:
        assert "only supports joint_move" in str(exc)
    else:
        raise AssertionError("RobotAction should reject unsupported action_type")
