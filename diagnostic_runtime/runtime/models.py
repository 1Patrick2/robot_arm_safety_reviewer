from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DiagnosticRuntimeRequest:
    """Request to run the full diagnostic runtime on an episode."""

    context_path: Path
    output_dir: Path
    provider: str = "fake"
    run_agent: bool = False


@dataclass(frozen=True)
class DiagnosticRuntimeResult:
    """Result of a diagnostic runtime run."""

    context_path: Path
    deterministic_report_path: Path
    agent_report_path: Path | None
    trace_path: Path
    safety_violations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_path": str(self.context_path),
            "deterministic_report_path": str(self.deterministic_report_path),
            "agent_report_path": str(self.agent_report_path) if self.agent_report_path else None,
            "trace_path": str(self.trace_path),
            "safety_violations": list(self.safety_violations),
        }
