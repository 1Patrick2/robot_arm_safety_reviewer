from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExternalTrajectoryRecord:
    """A structured record of an external trajectory imported into the safety pipeline."""

    schema_version: str = "external_trajectory_record.v1"
    dataset_name: str = ""
    episode_id: str = ""
    robot_name: str | None = None
    action_type: str = ""
    frame_count: int = 0
    mapping: dict[str, Any] = field(default_factory=dict)
    source_path: str = ""
    sequence_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_name": self.dataset_name,
            "episode_id": self.episode_id,
            "robot_name": self.robot_name,
            "action_type": self.action_type,
            "frame_count": self.frame_count,
            "mapping": dict(self.mapping),
            "source_path": self.source_path,
            "sequence_id": self.sequence_id,
            "metadata": dict(self.metadata),
        }


def write_external_trajectory_record(
    record: ExternalTrajectoryRecord,
    output_path: Path,
) -> Path:
    """Write an ``ExternalTrajectoryRecord`` to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(record.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
