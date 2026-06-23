import pytest

from bench.adapters.external_trajectory import (
    ExternalActionFrame,
    ExternalTrajectory,
    ActionMappingConfig,
    external_trajectory_to_policy_sequence,
)


def _make_trajectory(actions, action_type="joint_position"):
    return ExternalTrajectory(
        dataset_name="test",
        episode_id="ep1",
        action_type=action_type,
        frames=tuple(
            ExternalActionFrame(i, tuple(a), action_type, "test")
            for i, a in enumerate(actions)
        ),
    )


class TestExternalTrajectoryMapping:
    def test_converts_to_policy_sequence(self):
        traj = _make_trajectory([[0.1, 0.2, 0.0, 0.0, 0.0, 0.0]])
        mapping = ActionMappingConfig(joint_count=6)
        seq = external_trajectory_to_policy_sequence(traj, mapping)
        assert seq.sequence_id == "test__ep1"
        assert len(seq.actions) == 1
        assert seq.actions[0].action_type == "joint_target"

    def test_dimension_mismatch_raises(self):
        traj = _make_trajectory([[0.1, 0.2]])  # 2D, but mapping expects 6
        mapping = ActionMappingConfig(joint_count=6)
        with pytest.raises(ValueError, match="dimension"):
            external_trajectory_to_policy_sequence(traj, mapping)

    def test_scale_offset_applied(self):
        traj = _make_trajectory([[1.0, 1.0, 0.0, 0.0, 0.0, 0.0]])
        mapping = ActionMappingConfig(joint_count=6, scale=2.0, offset=(1.0, 1.0, 0.0, 0.0, 0.0, 0.0))
        seq = external_trajectory_to_policy_sequence(traj, mapping)
        mapped = seq.actions[0].values
        assert mapped[0] == 3.0  # 1.0 * 2.0 + 1.0
        assert mapped[1] == 3.0

    def test_previous_target_policy(self):
        traj = _make_trajectory([
            [0.1, 0.2, 0.0, 0.0, 0.0, 0.0],
            [0.3, 0.4, 0.0, 0.0, 0.0, 0.0],
        ])
        mapping = ActionMappingConfig(joint_count=6)
        seq = external_trajectory_to_policy_sequence(traj, mapping)
        assert seq is not None
        assert len(seq.actions) == 2

    def test_zeros_policy(self):
        traj = _make_trajectory([
            [0.1, 0.0, 0.0, 0.0, 0.0, 0.0],
        ])
        mapping = ActionMappingConfig(joint_count=6, current_joints_policy="zeros")
        seq = external_trajectory_to_policy_sequence(traj, mapping)
        assert seq is not None

    def test_unsupported_action_type_raises(self):
        traj = _make_trajectory([[0.1]], action_type="end_effector_delta")
        mapping = ActionMappingConfig(joint_count=1, source_action_type="joint_position")
        with pytest.raises(ValueError, match="Unsupported"):
            external_trajectory_to_policy_sequence(traj, mapping)
