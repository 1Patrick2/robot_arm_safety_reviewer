from __future__ import annotations

import json
from pathlib import Path

from robot.runtime.action_sequence import PolicyActionSequence


def _normalise(raw: dict) -> dict:
    """Convert LeRobot-style *episode_id* to *sequence_id* in place."""
    if "episode_id" in raw and "sequence_id" not in raw:
        raw["sequence_id"] = raw.pop("episode_id")
    return raw


class LeRobotStyleAdapter:
    """Adapter for local LeRobot-style episode directories.

    Expected layout under *source*::

        source/
          meta.json
          episodes/
            episode_000001.json
            episode_000002.json
            ...

    Each episode JSON contains an ``initial_joints`` list, an ``actions`` list,
    and optional ``language_instruction`` / ``metadata``.
    """

    name: str = "lerobot_style"

    @staticmethod
    def list_sequences(source: Path) -> list[str]:
        source = Path(source)
        episode_dir = source / "episodes"
        if not episode_dir.is_dir():
            return []
        ids: list[str] = []
        for child in sorted(episode_dir.iterdir()):
            if child.suffix != ".json":
                continue
            try:
                raw = json.loads(child.read_text(encoding="utf-8"))
                _normalise(raw)
                seq = PolicyActionSequence.from_dict(raw)
                ids.append(seq.sequence_id)
            except Exception:
                continue
        return ids

    @staticmethod
    def load_sequence(source: Path, sequence_id: str) -> PolicyActionSequence:
        source = Path(source)
        episode_dir = source / "episodes"
        if not episode_dir.is_dir():
            raise FileNotFoundError(f"episodes directory not found: {episode_dir}")

        # Quick ID match first, then let full validation propagate.
        for child in episode_dir.iterdir():
            if child.suffix != ".json":
                continue
            try:
                raw = json.loads(child.read_text(encoding="utf-8"))
            except Exception:
                continue
            ep_id = raw.get("episode_id") or raw.get("sequence_id")
            if ep_id != sequence_id:
                continue
            _normalise(raw)
            return PolicyActionSequence.from_dict(raw)

        raise KeyError(f"sequence not found: {sequence_id}")
