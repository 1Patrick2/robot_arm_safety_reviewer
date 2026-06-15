import pytest
from pathlib import Path

from dataset_adapters.mini_sequence_adapter import MiniSequenceAdapter

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "policy_sequences"


class TestMiniSequenceAdapter:
    def test_name(self):
        assert MiniSequenceAdapter.name == "mini_sequence"

    def test_list_sequences_returns_expected_ids(self):
        ids = MiniSequenceAdapter.list_sequences(SAMPLES)
        assert "simple_safe_sequence_001" in ids
        assert "near_miss_sequence_001" in ids
        assert "collision_sequence_001" in ids
        assert len(ids) == 3

    def test_list_sequences_returns_empty_for_nonexistent_dir(self, tmp_path):
        ids = MiniSequenceAdapter.list_sequences(tmp_path / "nonexistent")
        assert ids == []

    def test_load_sequence_returns_policy_action_sequence(self):
        seq = MiniSequenceAdapter.load_sequence(SAMPLES, "simple_safe_sequence_001")
        assert seq.sequence_id == "simple_safe_sequence_001"
        assert seq.source == "mini_fixture"
        assert len(seq.actions) == 2
        assert seq.actions[0].action_type == "joint_target"
        assert seq.actions[1].action_type == "delta_joint"

    def test_load_sequence_raises_for_missing_sequence(self):
        with pytest.raises(KeyError, match="nonexistent_sequence"):
            MiniSequenceAdapter.load_sequence(SAMPLES, "nonexistent_sequence")

    def test_load_sequence_raises_for_nonexistent_source(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            MiniSequenceAdapter.load_sequence(tmp_path / "nonexistent", "any_id")
