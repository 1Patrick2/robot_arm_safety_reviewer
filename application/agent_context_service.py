from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from diagnostics.context.builder import build_agent_context_from_db
from diagnostics.context.models import AgentContext
from diagnostics.context.render import write_agent_context_files
from application.core import AppResult, ArtifactRef

DEFAULT_DB = Path("output_reports/runtime_metrics/runtime_metrics.db")


@dataclass(frozen=True)
class AgentContextBuildRequest:
    episode_id: str
    db_path: Path = DEFAULT_DB
    output_dir: Path | None = None
    max_steps: int = 10


@dataclass(frozen=True)
class AgentContextBuildResult:
    context: AgentContext
    json_path: Path | None
    markdown_path: Path | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.context.episode_id,
            "sequence_id": self.context.sequence_id,
            "total_steps": self.context.total_steps,
            "critical_step_count": len(self.context.critical_steps),
            "json_path": str(self.json_path) if self.json_path else None,
            "markdown_path": str(self.markdown_path) if self.markdown_path else None,
        }

    def to_app_result(self) -> AppResult:
        artifacts: list[ArtifactRef] = []
        if self.json_path:
            artifacts.append(
                ArtifactRef(kind="diagnostic_context_json", path=self.json_path, description="Diagnostic context JSON")
            )
        if self.markdown_path:
            artifacts.append(
                ArtifactRef(kind="diagnostic_context_markdown", path=self.markdown_path, description="Diagnostic context Markdown")
            )
        return AppResult(
            ok=True,
            mode="agent_context_build",
            data=self.to_dict(),
            artifacts=tuple(artifacts),
        )


def build_agent_context(request: AgentContextBuildRequest) -> AgentContextBuildResult:
    """Build a diagnostic AgentContext and write output files."""
    context = build_agent_context_from_db(
        db_path=request.db_path,
        episode_id=request.episode_id,
        max_steps=request.max_steps,
    )

    json_path: Path | None = None
    markdown_path: Path | None = None
    if request.output_dir:
        json_path, markdown_path = write_agent_context_files(context, request.output_dir)

    return AgentContextBuildResult(
        context=context,
        json_path=json_path,
        markdown_path=markdown_path,
    )
