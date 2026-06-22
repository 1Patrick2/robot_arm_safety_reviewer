from __future__ import annotations

import json
from pathlib import Path

from robot.runtime.action_sequence import PolicyActionSequence

from .base import DatasetAdapter


class MiniSequenceAdapter:
    """Adapter for local samples/policy_sequences/*.json fixtures.

    Each file in *source* is expected to be a valid PolicyActionSequence JSON file.
    The sequence ID is read from the file content so that filenames and IDs can
    diverge when needed.
    """

    name: str = "mini_sequence"

    @staticmethod
    def list_sequences(source: Path) -> list[str]:
        source = Path(source)
        if not source.is_dir():
            return []
        ids: list[str] = []
        for child in sorted(source.iterdir()):
            if child.suffix != ".json":
                continue
            try:
                seq = PolicyActionSequence.from_json(child)
                ids.append(seq.sequence_id)
            except Exception:
                continue
        return ids

    @staticmethod
    def load_sequence(source: Path, sequence_id: str) -> PolicyActionSequence:
        source = Path(source)
        if not source.is_dir():
            raise FileNotFoundError(f"source directory not found: {source}")
        for child in source.iterdir():
            if child.suffix != ".json":
                continue
            try:
                raw = json.loads(child.read_text(encoding="utf-8"))
            except Exception:
                continue
            if raw.get("sequence_id") != sequence_id:
                continue
            # Found the target file — use full validation and let any
            # parse/validation error propagate.
            return PolicyActionSequence.from_dict(raw)
        raise KeyError(f"sequence not found: {sequence_id}")
