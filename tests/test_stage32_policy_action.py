import json
from pathlib import Path

import pytest

from robot_runtime.action_sequence import PolicyActionSequence
from robot_runtime.policy_action import PolicyAction, policy_action_to_robot_action
from robot_runtime.types import RobotObservation


def make_observation(joints=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5)) -> RobotObservation:
    return RobotObservation(
        robot_id="mock_realman",
        joint_positions=joints,
        timestamp="2026-06-12T00:00:00+00:00",
    )


def test_load_policy_action_sequence_from_json(tmp_path):
    path = tmp_path / "sequence.json"
    path.write_text(
        json.dumps(
            {
                "sequence_id": "simple_safe_sequence_001",
                "source": "mini_fixture",
                "initial_joints": [0, 0, 0, 0, 0, 0],
                "language_instruction": "move to a safe nearby joint target",
                "metadata": {"difficulty": "easy"},
                "actions": [
                    {
                        "action_type": "joint_target",
                        "values": [0.1, 0.2, 0, 0, 0, 0],
                        "timestamp": 0.0,
                        "metadata": {"step_name": "safe_move_1"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    sequence = PolicyActionSequence.from_json(path)

    assert sequence.sequence_id == "simple_safe_sequence_001"
    assert sequence.source == "mini_fixture"
    assert sequence.initial_joints == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert sequence.language_instruction == "move to a safe nearby joint target"
    assert sequence.metadata == {"difficulty": "easy"}
    assert sequence.actions[0].action_type == "joint_target"
    assert sequence.actions[0].values == (0.1, 0.2, 0.0, 0.0, 0.0, 0.0)
    assert sequence.actions[0].metadata == {"step_name": "safe_move_1"}


def test_policy_action_sequence_to_dict_round_trips_values():
    sequence = PolicyActionSequence(
        sequence_id="delta_sequence_001",
        initial_joints=(0, 0, 0, 0, 0, 0),
        actions=(
            PolicyAction(
                action_type="delta_joint",
                values=(0.1, 0, 0, 0, 0, 0),
                timestamp=1.5,
                metadata={"step_name": "nudge_joint_1"},
            ),
        ),
        source="unit_test",
        language_instruction="nudge joint one",
        metadata={"split": "test"},
    )

    assert sequence.to_dict() == {
        "sequence_id": "delta_sequence_001",
        "source": "unit_test",
        "initial_joints": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "language_instruction": "nudge joint one",
        "metadata": {"split": "test"},
        "actions": [
            {
                "action_type": "delta_joint",
                "values": [0.1, 0.0, 0.0, 0.0, 0.0, 0.0],
                "timestamp": 1.5,
                "metadata": {"step_name": "nudge_joint_1"},
            }
        ],
    }


def test_joint_target_action_to_robot_action():
    action = PolicyAction(
        action_type="joint_target",
        values=(0.2, 0.3, 0.4, 0.5, 0.6, 0.7),
        metadata={"source_step": 2},
    )

    robot_action = policy_action_to_robot_action(make_observation(), action)

    assert robot_action.action_type == "joint_move"
    assert robot_action.target_joints == (0.2, 0.3, 0.4, 0.5, 0.6, 0.7)
    assert robot_action.source == "policy_action"
    assert robot_action.metadata["policy_action_type"] == "joint_target"
    assert robot_action.metadata["source_step"] == 2


def test_delta_joint_action_to_robot_action():
    action = PolicyAction(
        action_type="delta_joint",
        values=(0.1, -0.1, 0, 0.2, 0, -0.2),
    )

    robot_action = policy_action_to_robot_action(make_observation(), action)

    assert robot_action.target_joints == pytest.approx((0.1, 0.0, 0.2, 0.5, 0.4, 0.3))
    assert robot_action.metadata["policy_action_type"] == "delta_joint"


def test_invalid_action_type_raises():
    action = PolicyAction(action_type="ee_pose", values=(0, 0, 0, 0, 0, 0))

    with pytest.raises(ValueError, match="Unsupported policy action type"):
        policy_action_to_robot_action(make_observation(), action)


def test_action_dimension_mismatch_raises():
    with pytest.raises(ValueError, match="values must contain six values"):
        PolicyAction(action_type="joint_target", values=(0, 0, 0))


def test_sequence_requires_at_least_one_action():
    with pytest.raises(ValueError, match="actions must contain at least one action"):
        PolicyActionSequence(
            sequence_id="empty",
            initial_joints=(0, 0, 0, 0, 0, 0),
            actions=(),
            source="unit_test",
        )
