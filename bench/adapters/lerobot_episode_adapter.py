from __future__ import annotations

import json
from pathlib import Path

from bench.adapters.external_trajectory import (
    ExternalActionFrame,
    ExternalTrajectory,
)


def load_lerobot_style_episode(path: str | Path) -> ExternalTrajectory:
    """Load a local LeRobot-style episode JSON into an ``ExternalTrajectory``.

    Expected JSON format::

        {
          "dataset_name": "lerobot_style_sample",
          "episode_id": "episode_000001",
          "robot_name": "aloha_like",
          "action_type": "joint_position",
          "actions": [[...], [...]],
          "timestamps": [0.0, 0.1],
          "metadata": {}
        }

    Args:
        path: Path to the episode JSON file.

    Returns:
        An ``ExternalTrajectory`` instance.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If validation fails.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"episode not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise ValueError("episode JSON root must be a dict")

    dataset_name = raw.get("dataset_name")
    if not dataset_name or not isinstance(dataset_name, str):
        raise ValueError("missing or invalid 'dataset_name' (must be non-empty string)")

    episode_id = raw.get("episode_id")
    if not episode_id or not isinstance(episode_id, str):
        raise ValueError("missing or invalid 'episode_id' (must be non-empty string)")

    action_type = raw.get("action_type")
    if not action_type or not isinstance(action_type, str):
        raise ValueError("missing or invalid 'action_type' (must be non-empty string)")

    actions_raw = raw.get("actions")
    if not isinstance(actions_raw, list) or len(actions_raw) == 0:
        raise ValueError("'actions' must be a non-empty list")

    timestamps_raw = raw.get("timestamps")
    if timestamps_raw is not None:
        if not isinstance(timestamps_raw, list):
            raise ValueError("'timestamps' must be a list or null")
        if len(timestamps_raw) != len(actions_raw):
            raise ValueError(
                f"timestamps length {len(timestamps_raw)} != "
                f"actions length {len(actions_raw)}"
            )

    frames: list[ExternalActionFrame] = []
    for fi, act_raw in enumerate(actions_raw):
        if not isinstance(act_raw, list):
            raise ValueError(f"actions[{fi}] must be a list")
        if any(not isinstance(v, (int, float)) for v in act_raw):
            raise ValueError(f"actions[{fi}] contains non-numeric values")
        ts = float(timestamps_raw[fi]) if timestamps_raw else None
        frames.append(ExternalActionFrame(
            step_index=fi,
            action=tuple(float(v) for v in act_raw),
            action_type=action_type,
            source="lerobot_style",
            timestamp=ts,
        ))

    return ExternalTrajectory(
        dataset_name=dataset_name,
        episode_id=episode_id,
        robot_name=raw.get("robot_name"),
        action_type=action_type,
        frames=tuple(frames),
        metadata=raw.get("metadata", {}),
    )
