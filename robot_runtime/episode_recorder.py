from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .types import RuntimeStepResult


class EpisodeRecorder:
    schema_version = "stage3.runtime_episode.v1"

    def __init__(
        self,
        *,
        root_dir: str | Path,
        robot_name: str,
        action_source_name: str,
        scene_provider_name: str,
        backend_name: str,
        episode_id: str | None = None,
    ) -> None:
        self.root_dir = Path(root_dir)
        self.episode_id = episode_id or self._make_episode_id()
        self.episode_dir = self.root_dir / self.episode_id
        self.episode_dir.mkdir(parents=True, exist_ok=True)
        self.steps_path = self.episode_dir / "steps.jsonl"
        self.metadata_path = self.episode_dir / "metadata.json"
        self._write_metadata(
            robot_name=robot_name,
            action_source_name=action_source_name,
            scene_provider_name=scene_provider_name,
            backend_name=backend_name,
        )

    def record_step(self, result: RuntimeStepResult) -> Path:
        with self.steps_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(result.to_dict(), indent=None) + "\n")
        return self.steps_path

    def _write_metadata(
        self,
        *,
        robot_name: str,
        action_source_name: str,
        scene_provider_name: str,
        backend_name: str,
    ) -> None:
        payload = {
            "schema_version": self.schema_version,
            "episode_id": self.episode_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "robot": robot_name,
            "action_source": action_source_name,
            "scene_provider": scene_provider_name,
            "backend": backend_name,
        }
        self.metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _make_episode_id() -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"episode_{stamp}_{uuid4().hex[:8]}"
