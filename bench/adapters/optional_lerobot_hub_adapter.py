"""Optional LeRobot Hub episode loader — uses lazy import and is not part of core tests.

Requires: pip install lerobot
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bench.adapters.external_trajectory import (
    ExternalActionFrame,
    ExternalTrajectory,
)


def load_lerobot_hub_episode(
    repo_id: str,
    episode_index: int = 0,
    max_frames: int | None = None,
    action_key: str = "action",
) -> ExternalTrajectory:
    """Load one episode from a LeRobot dataset on Hugging Face Hub.

    This function lazy-imports ``lerobot``. It requires the optional
    dependency to be installed: ``pip install lerobot``.

    Args:
        repo_id: Hugging Face dataset repo ID (e.g. ``"lerobot/aloha_mobile_cabinet"``).
        episode_index: Which episode to load from the dataset.
        max_frames: Maximum number of frames to include (``None`` = all).
        action_key: Key for action data in the dataset frames.

    Returns:
        An ``ExternalTrajectory`` with the extracted action frames.

    Raises:
        RuntimeError: If ``lerobot`` is not installed.
    """
    try:
        from lerobot.common.datasets.lerobot_dataset import LeRobotDataset  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "load_lerobot_hub_episode requires optional dependency 'lerobot'. "
            "Install with: pip install lerobot"
        ) from exc

    dataset = LeRobotDataset(repo_id)
    episode_data = dataset[episode_index]

    actions = _to_list(episode_data[action_key])
    total = len(actions)
    if max_frames is not None:
        actions = actions[:max_frames]

    frames: list[ExternalActionFrame] = []
    for fi, act in enumerate(actions):
        action_tuple = tuple(float(v) for v in act)
        frames.append(ExternalActionFrame(
            step_index=fi,
            action=action_tuple,
            action_type="joint_position_6d",
            source="lerobot_hub",
            timestamp=float(fi),
        ))

    return ExternalTrajectory(
        dataset_name=repo_id.replace("/", "_"),
        episode_id=f"episode_{episode_index:06d}",
        action_type="joint_position_6d",
        frames=tuple(frames),
        robot_name=repo_id.split("/")[-1] if "/" in repo_id else repo_id,
        metadata={
            "source": "lerobot_hub",
            "repo_id": repo_id,
            "episode_index": episode_index,
            "total_frames": total,
            "loaded_frames": len(frames),
        },
    )


def _to_list(value: Any) -> list:
    """Convert a tensor/array to a Python list."""
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "numpy"):
        return value.numpy().tolist()
    return list(value)
