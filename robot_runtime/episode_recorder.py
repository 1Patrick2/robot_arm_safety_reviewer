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
        run_mode: str = "sequence_runtime",
        artifact_schema_version: str = "stage3.visual_sandbox.v1",
        sequence_id: str | None = None,
        device_name: str | None = None,
        pipeline_stage: str = "stage3.6_runtime_metrics_db",
        scene_path: str | None = None,
    ) -> None:
        self.root_dir = Path(root_dir)
        self.episode_id = episode_id or self._make_episode_id()
        self.episode_dir = self.root_dir / self.episode_id
        self.episode_dir.mkdir(parents=True, exist_ok=True)
        self.steps_path = self.episode_dir / "steps.jsonl"
        self.metadata_path = self.episode_dir / "metadata.json"
        self._step_count = 0
        self._write_metadata(
            robot_name=robot_name,
            action_source_name=action_source_name,
            scene_provider_name=scene_provider_name,
            backend_name=backend_name,
            run_mode=run_mode,
            artifact_schema_version=artifact_schema_version,
            sequence_id=sequence_id,
            device_name=device_name,
            pipeline_stage=pipeline_stage,
            scene_path=scene_path,
        )

    def record_step(self, result: RuntimeStepResult) -> Path:
        self._step_count += 1
        payload = result.to_dict()
        if payload["episode_id"] is None:
            payload["episode_id"] = self.episode_id
        if payload["step_index"] is None:
            payload["step_index"] = self._step_count
        with self.steps_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, indent=None) + "\n")
        return self.steps_path

    def _write_metadata(
        self,
        *,
        robot_name: str,
        action_source_name: str,
        scene_provider_name: str,
        backend_name: str,
        run_mode: str = "sequence_runtime",
        artifact_schema_version: str = "stage3.visual_sandbox.v1",
        sequence_id: str | None = None,
        device_name: str | None = None,
        pipeline_stage: str = "stage3.6_runtime_metrics_db",
        scene_path: str | None = None,
    ) -> None:
        payload = {
            "schema_version": self.schema_version,
            "episode_id": self.episode_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "robot": robot_name,
            "device": device_name,
            "action_source": action_source_name,
            "scene_provider": scene_provider_name,
            "backend": backend_name,
            "run_mode": run_mode,
            "artifact_schema_version": artifact_schema_version,
            "pipeline_stage": pipeline_stage,
            "sequence_id": sequence_id,
            "scene_path": scene_path,
            "project_stage": "stage3_runtime_mvp",
            "notes": None,
        }
        self.metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _make_episode_id() -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"episode_{stamp}_{uuid4().hex[:8]}"
