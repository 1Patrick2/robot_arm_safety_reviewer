import json
from pathlib import Path

import pytest

from robot.runtime.episode_loader import (
    RuntimeEpisodeBundle,
    load_episode,
    load_episode_metadata,
    load_episode_steps,
)


def _write_episode(
    episode_dir: Path,
    *,
    metadata: dict | None = None,
    steps: list[dict] | None = None,
) -> Path:
    episode_dir.mkdir(parents=True, exist_ok=True)
    meta = metadata or {"episode_id": "test_episode", "backend": "mock", "robot": "mock_realman"}
    (episode_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    steps_data = steps or [
        {
            "step_id": "step_000001",
            "observation": {"robot_id": "mock_realman_6dof", "joint_positions": [0, 0, 0, 0, 0, 0], "timestamp": "2026-01-01T00:00:00Z"},
            "proposed_action": {"action_type": "joint_move", "target_joints": [0.1, 0.1, 0, 0, 0, 0], "speed": 0.1, "source": "replay"},
            "safety_result": {"decision": "approve", "risk_level": "low"},
            "executed": True,
            "blocked_reason": None,
        }
    ]
    with (episode_dir / "steps.jsonl").open("w", encoding="utf-8") as handle:
        for step in steps_data:
            handle.write(json.dumps(step, indent=None) + "\n")
    return episode_dir


class TestLoadEpisodeSteps:
    def test_loads_steps_from_jsonl(self, tmp_path):
        ep_dir = _write_episode(tmp_path / "ep_001")
        steps = load_episode_steps(ep_dir)
        assert len(steps) == 1
        assert steps[0]["step_id"] == "step_000001"
        assert steps[0]["safety_result"]["decision"] == "approve"

    def test_missing_steps_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="steps.jsonl"):
            load_episode_steps(tmp_path / "nonexistent")


class TestLoadEpisodeMetadata:
    def test_loads_metadata(self, tmp_path):
        ep_dir = _write_episode(tmp_path / "ep_002")
        meta = load_episode_metadata(ep_dir)
        assert meta["episode_id"] == "test_episode"
        assert meta["backend"] == "mock"

    def test_missing_metadata_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="metadata.json"):
            load_episode_metadata(tmp_path / "nonexistent")


class TestLoadEpisode:
    def test_loads_bundle(self, tmp_path):
        ep_dir = _write_episode(tmp_path / "ep_003")
        bundle = load_episode(ep_dir)
        assert isinstance(bundle, RuntimeEpisodeBundle)
        assert bundle.episode_dir == ep_dir
        assert bundle.metadata["episode_id"] == "test_episode"
        assert len(bundle.steps) == 1

    def test_missing_directory_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_episode(tmp_path / "nonexistent")
