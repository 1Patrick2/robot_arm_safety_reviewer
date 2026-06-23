import json
from pathlib import Path

import pytest

from bench.adapters.lerobot_style_adapter import LeRobotStyleAdapter

SAMPLES = Path(__file__).resolve().parents[1] / "bench" / "samples" / "lerobot_style"


class TestLeRobotStyleAdapter:
    def test_name(self):
        assert LeRobotStyleAdapter.name == "lerobot_style"

    def test_list_sequences_returns_expected_ids(self):
        ids = LeRobotStyleAdapter.list_sequences(SAMPLES)
        assert "episode_000001" in ids
        assert len(ids) == 1

    def test_list_sequences_returns_empty_for_nonexistent_source(self, tmp_path):
        ids = LeRobotStyleAdapter.list_sequences(tmp_path / "nonexistent")
        assert ids == []

    def test_load_sequence_returns_policy_action_sequence(self):
        seq = LeRobotStyleAdapter.load_sequence(SAMPLES, "episode_000001")
        assert seq.sequence_id == "episode_000001"
        assert len(seq.actions) == 2
        assert seq.actions[0].action_type == "joint_target"
        assert seq.actions[1].action_type == "delta_joint"
        assert seq.language_instruction == "move joints through two small safe targets"
        assert seq.initial_joints == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def test_load_sequence_raises_for_missing_sequence(self):
        with pytest.raises(KeyError, match="nonexistent"):
            LeRobotStyleAdapter.load_sequence(SAMPLES, "nonexistent")

    def test_load_sequence_raises_for_nonexistent_source(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            LeRobotStyleAdapter.load_sequence(tmp_path / "nonexistent", "any_id")

    def test_load_sequence_raises_for_corrupt_episode_id(self, tmp_path):
        # Create an episode file with a mismatched filename but wrong ID
        ep_dir = tmp_path / "episodes"
        ep_dir.mkdir(parents=True)
        ep_file = ep_dir / "bad_episode.json"
        ep_file.write_text(
            json.dumps({
                "episode_id": "other_id",
                "source": "test",
                "initial_joints": [0, 0, 0, 0, 0, 0],
                "actions": [{"action_type": "joint_target", "values": [0.1, 0.1, 0, 0, 0, 0]}],
            }),
            encoding="utf-8",
        )
        # load_sequence with the correct ID must find it
        seq = LeRobotStyleAdapter.load_sequence(tmp_path, "other_id")
        assert seq.sequence_id == "other_id"

    def test_load_sequence_exposes_corrupt_file_error(self, tmp_path):
        # Create an episode file that is valid JSON but has invalid content
        ep_dir = tmp_path / "episodes"
        ep_dir.mkdir(parents=True)
        ep_file = ep_dir / "episode_corrupt.json"
        ep_file.write_text(
            json.dumps({
                "episode_id": "episode_corrupt",
                "source": "test",
                "initial_joints": [0, 0],
                "actions": [],
            }),
            encoding="utf-8",
        )
        # Should raise ValueError (initial_joints must contain six values)
        with pytest.raises(ValueError, match="must contain six values"):
            LeRobotStyleAdapter.load_sequence(tmp_path, "episode_corrupt")
