from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeEpisodeBundle:
    episode_dir: Path
    metadata: dict[str, Any]
    steps: tuple[dict[str, Any], ...]


def load_episode_steps(episode_dir: Path) -> list[dict[str, Any]]:
    """Read *steps.jsonl* from *episode_dir* and return each line as a dict."""
    steps_path = Path(episode_dir) / "steps.jsonl"
    if not steps_path.exists():
        raise FileNotFoundError(f"steps.jsonl not found: {steps_path}")
    steps: list[dict[str, Any]] = []
    with steps_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            steps.append(json.loads(line))
    return steps


def load_episode_metadata(episode_dir: Path) -> dict[str, Any]:
    """Read *metadata.json* from *episode_dir* and return its contents."""
    meta_path = Path(episode_dir) / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json not found: {meta_path}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def load_episode(episode_dir: Path) -> RuntimeEpisodeBundle:
    """Load both metadata and steps from *episode_dir*."""
    metadata = load_episode_metadata(episode_dir)
    steps = load_episode_steps(episode_dir)
    return RuntimeEpisodeBundle(
        episode_dir=Path(episode_dir),
        metadata=metadata,
        steps=tuple(steps),
    )
