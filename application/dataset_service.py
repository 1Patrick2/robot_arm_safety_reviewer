from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dataset_adapters.mini_sequence_adapter import MiniSequenceAdapter
from robot_runtime.action_sequence import PolicyActionSequence

from .core import AppResult, ArtifactRef


def _get_adapter(adapter_name: str):
    """Return an adapter instance for *adapter_name*.

    Currently only *mini_sequence* is supported.
    """
    mapping = {
        "mini_sequence": MiniSequenceAdapter,
    }
    cls = mapping.get(adapter_name)
    if cls is None:
        raise ValueError(f"unsupported dataset adapter: {adapter_name}")
    return cls()


@dataclass(frozen=True)
class DatasetListRequest:
    adapter_name: str = "mini_sequence"
    source: Path = Path("samples/policy_sequences")


@dataclass(frozen=True)
class DatasetListResult:
    adapter_name: str
    source: Path
    sequence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter_name,
            "source": str(self.source),
            "sequence_ids": list(self.sequence_ids),
            "count": len(self.sequence_ids),
        }


@dataclass(frozen=True)
class DatasetExportSequenceRequest:
    adapter_name: str = "mini_sequence"
    source: Path = Path("samples/policy_sequences")
    sequence_id: str = ""
    output: Path | None = None


@dataclass(frozen=True)
class DatasetExportSequenceResult:
    adapter_name: str
    sequence_id: str
    exported_path: Path | None
    sequence: PolicyActionSequence | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter_name,
            "sequence_id": self.sequence_id,
            "exported_path": str(self.exported_path) if self.exported_path else None,
            "sequence": self.sequence.to_dict() if self.sequence else None,
        }

    def to_app_result(self) -> AppResult:
        artifacts: tuple[ArtifactRef, ...] = ()
        if self.exported_path:
            artifacts = (
                ArtifactRef(
                    kind="exported_sequence",
                    path=self.exported_path,
                    description=f"Exported sequence: {self.sequence_id}",
                ),
            )
        return AppResult(
            ok=True,
            mode="dataset_export_sequence",
            data=self.to_dict(),
            artifacts=artifacts,
        )


def dataset_list(request: DatasetListRequest) -> DatasetListResult:
    adapter = _get_adapter(request.adapter_name)
    ids = adapter.list_sequences(request.source)
    return DatasetListResult(
        adapter_name=request.adapter_name,
        source=request.source,
        sequence_ids=tuple(ids),
    )


def dataset_export_sequence(request: DatasetExportSequenceRequest) -> DatasetExportSequenceResult:
    adapter = _get_adapter(request.adapter_name)
    sequence = adapter.load_sequence(request.source, request.sequence_id)

    exported_path: Path | None = None
    if request.output is not None:
        output = Path(request.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(sequence.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        exported_path = output

    return DatasetExportSequenceResult(
        adapter_name=request.adapter_name,
        sequence_id=request.sequence_id,
        exported_path=exported_path,
        sequence=sequence if not exported_path else None,
    )
