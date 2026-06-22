from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import json


@dataclass(frozen=True)
class PerceptionInferenceRecord:
    """A structured record of a single perception inference run.

    Records the adapter, input, latency, perception result, safety
    observations, and fusion outcome. Designed to be written as JSON
    and indexed by ``evidence_manifest.json``.
    """

    schema_version: str = "perception_inference_record.v1"
    adapter_name: str = ""
    adapter_kind: str = ""
    input_path: str = ""
    input_exists: bool = False
    sequence_id: str | None = None
    frame_id: str = ""
    latency_ms: float = 0.0
    perception_result: dict[str, Any] = field(default_factory=dict)
    safety_observations: tuple[dict[str, Any], ...] = ()
    fusion_result: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_name": self.adapter_name,
            "adapter_kind": self.adapter_kind,
            "input_path": self.input_path,
            "input_exists": self.input_exists,
            "sequence_id": self.sequence_id,
            "frame_id": self.frame_id,
            "latency_ms": self.latency_ms,
            "perception_result": self.perception_result,
            "safety_observations": list(self.safety_observations),
            "fusion_result": self.fusion_result,
            "metadata": dict(self.metadata),
        }


def write_perception_inference_record(
    record: PerceptionInferenceRecord,
    output_path: Path,
) -> Path:
    """Write a ``PerceptionInferenceRecord`` to a JSON file.

    Args:
        record: The record to write.
        output_path: Destination path.

    Returns:
        *output_path* for chaining.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(record.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
