import json
from pathlib import Path

import pytest

from bench.adapters.lerobot_episode_adapter import load_lerobot_style_episode


SAMPLE = {
    "dataset_name": "test_ds",
    "episode_id": "ep_001",
    "robot_name": "aloha",
    "action_type": "joint_position",
    "actions": [[0.1, 0.2], [0.3, 0.4]],
    "timestamps": [0.0, 0.1],
}


def _write(tmp_path, data) -> Path:
    p = tmp_path / "episode.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


class TestLoadLerobotStyleEpisode:
    def test_load_valid(self, tmp_path):
        p = _write(tmp_path, SAMPLE)
        traj = load_lerobot_style_episode(p)
        assert traj.dataset_name == "test_ds"
        assert traj.episode_id == "ep_001"
        assert traj.action_type == "joint_position"
        assert len(traj.frames) == 2

    def test_missing_dataset_name(self, tmp_path):
        d = dict(SAMPLE); del d["dataset_name"]
        with pytest.raises(ValueError, match="dataset_name"):
            load_lerobot_style_episode(_write(tmp_path, d))

    def test_missing_episode_id(self, tmp_path):
        d = dict(SAMPLE); del d["episode_id"]
        with pytest.raises(ValueError, match="episode_id"):
            load_lerobot_style_episode(_write(tmp_path, d))

    def test_empty_actions_fails(self, tmp_path):
        d = dict(SAMPLE); d["actions"] = []
        with pytest.raises(ValueError, match="actions"):
            load_lerobot_style_episode(_write(tmp_path, d))

    def test_timestamp_length_mismatch(self, tmp_path):
        d = dict(SAMPLE); d["timestamps"] = [0.0]
        with pytest.raises(ValueError, match="timestamps"):
            load_lerobot_style_episode(_write(tmp_path, d))

    def test_non_numeric_action_fails(self, tmp_path):
        d = {"dataset_name": "ds", "episode_id": "ep1", "action_type": "jp",
             "actions": [["a", "b"]]}
        with pytest.raises(ValueError, match="non-numeric"):
            load_lerobot_style_episode(_write(tmp_path, d))

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_lerobot_style_episode(tmp_path / "nonexistent.json")
