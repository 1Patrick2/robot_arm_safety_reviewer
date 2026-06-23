from __future__ import annotations

from pathlib import Path
from typing import Protocol

from robot.runtime.action_sequence import PolicyActionSequence


class DatasetAdapter(Protocol):
    """Protocol for dataset adapters that read PolicyActionSequence objects."""

    name: str

    def list_sequences(self, source: Path) -> list[str]:
        """Return a list of sequence IDs available at *source*."""
        ...

    def load_sequence(self, source: Path, sequence_id: str) -> PolicyActionSequence:
        """Load and return a single PolicyActionSequence by its ID."""
        ...
