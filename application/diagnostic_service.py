from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agent_context_service import build_agent_context, AgentContextBuildRequest
from diagnostic_runtime.runtime.models import DiagnosticRuntimeRequest
from diagnostic_runtime.runtime.runner import run_diagnostic_runtime
from .core import AppResult, ArtifactRef

DEFAULT_DB = Path("output_reports/runtime_metrics/runtime_metrics.db")


@dataclass(frozen=True)
class DiagnosticRunRequest:
    episode_id: str
    db_path: Path = DEFAULT_DB
    output_dir: Path = Path("output_reports/diagnostics")
    provider: str = "fake"
    max_steps: int = 10
    run_agent: bool = False


@dataclass(frozen=True)
class DiagnosticRunResult:
    context_path: Path
    context: dict[str, Any]
    deterministic_report_path: Path
    agent_report_path: Path | None
    trace_path: Path
    safety_violations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.context.get("episode_id"),
            "total_steps": self.context.get("total_steps"),
            "critical_step_count": len(self.context.get("critical_steps", [])),
            "deterministic_report_path": str(self.deterministic_report_path),
            "agent_report_path": str(self.agent_report_path) if self.agent_report_path else None,
            "trace_path": str(self.trace_path),
            "safety_violations": list(self.safety_violations),
        }

    def to_app_result(self) -> AppResult:
        artifacts = [
            ArtifactRef(kind="diagnostic_context", path=self.context_path, description="Diagnostic context JSON"),
            ArtifactRef(kind="deterministic_report", path=self.deterministic_report_path, description="Deterministic diagnostic report"),
        ]
        if self.agent_report_path:
            artifacts.append(
                ArtifactRef(kind="agent_report", path=self.agent_report_path, description="Diagnostic agent report")
            )
        artifacts.append(
            ArtifactRef(kind="diagnostic_trace", path=self.trace_path, description="Diagnostic runtime trace")
        )
        return AppResult(
            ok=True,
            mode="diagnostic_run",
            data=self.to_dict(),
            artifacts=tuple(artifacts),
        )


def run_diagnostic(request: DiagnosticRunRequest) -> DiagnosticRunResult:
    """Run the full diagnostic pipeline: build context -> deterministic report -> optional agent -> trace."""
    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build agent context from metrics DB
    ctx_result = build_agent_context(
        AgentContextBuildRequest(
            episode_id=request.episode_id,
            db_path=request.db_path,
            output_dir=output_dir / "context",
            max_steps=request.max_steps,
        )
    )
    context_path = ctx_result.json_path
    context = ctx_result.context

    # 2. Run diagnostic runtime on the context
    runtime_request = DiagnosticRuntimeRequest(
        context_path=context_path,
        output_dir=output_dir,
        provider=request.provider,
        run_agent=request.run_agent,
    )
    runtime_result = run_diagnostic_runtime(runtime_request)

    return DiagnosticRunResult(
        context_path=context_path,
        context=context.to_dict(),
        deterministic_report_path=runtime_result.deterministic_report_path,
        agent_report_path=runtime_result.agent_report_path,
        trace_path=runtime_result.trace_path,
        safety_violations=runtime_result.safety_violations,
    )
