from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agent_context_service import build_agent_context, AgentContextBuildRequest
from diagnostic_runtime.runtime.models import DiagnosticRuntimeRequest
from diagnostic_runtime.runtime.runner import run_diagnostic_runtime
from diagnostic_runtime.tools.context_tools import load_diagnostic_context
from diagnostic_runtime.report.deterministic import build_diagnostic_report
from diagnostic_runtime.runtime.trace import write_runtime_trace
from diagnostic_runtime.runtime.models import DiagnosticRuntimeResult as _RuntimeResult
from .core import AppResult, ArtifactRef

DEFAULT_DB = Path("output_reports/runtime_metrics/runtime_metrics.db")


# ── diagnostic run ───────────────────────────────────────────────────


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
            "context_path": str(self.context_path),
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
    episode_dir = Path(request.output_dir) / request.episode_id
    episode_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build agent context from metrics DB
    ctx_result = build_agent_context(
        AgentContextBuildRequest(
            episode_id=request.episode_id,
            db_path=request.db_path,
            output_dir=episode_dir / "context",
            max_steps=request.max_steps,
        )
    )
    if ctx_result.json_path is None:
        raise RuntimeError(f"agent context build failed: no json_path for episode {request.episode_id}")
    context_path = ctx_result.json_path
    context = ctx_result.context

    # 2. Run diagnostic runtime on the context
    runtime_request = DiagnosticRuntimeRequest(
        context_path=context_path,
        output_dir=episode_dir,
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


# ── diagnostic report (from existing context) ────────────────────────


@dataclass(frozen=True)
class DiagnosticReportRequest:
    context_path: Path
    output_dir: Path = Path("output_reports/diagnostics")


@dataclass(frozen=True)
class DiagnosticReportResult:
    context_path: Path
    deterministic_report_path: Path
    trace_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_path": str(self.context_path),
            "deterministic_report_path": str(self.deterministic_report_path),
            "trace_path": str(self.trace_path),
        }

    def to_app_result(self) -> AppResult:
        return AppResult(
            ok=True,
            mode="diagnostic_report",
            data=self.to_dict(),
            artifacts=(
                ArtifactRef(kind="deterministic_report", path=self.deterministic_report_path, description="Deterministic diagnostic report"),
                ArtifactRef(kind="diagnostic_trace", path=self.trace_path, description="Diagnostic runtime trace"),
            ),
        )


def run_diagnostic_report(request: DiagnosticReportRequest) -> DiagnosticReportResult:
    """Generate a deterministic diagnostic report and trace from an existing context file.
    Does not query the metrics DB or run an agent."""
    context_path = Path(request.context_path)
    if not context_path.exists():
        raise FileNotFoundError(f"context not found: {context_path}")

    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load context
    bundle = load_diagnostic_context(context_path)

    # 2. Build deterministic report
    report_md = build_diagnostic_report(bundle)
    report_path = output_dir / "diagnostic_report.md"
    report_path.write_text(report_md, encoding="utf-8")

    # 3. Build result + trace
    trace_path = output_dir / "diagnostic_runtime_trace.json"
    runtime_result = _RuntimeResult(
        context_path=context_path,
        deterministic_report_path=report_path,
        agent_report_path=None,
        trace_path=trace_path,
        safety_violations=(),
    )
    write_runtime_trace(runtime_result)

    return DiagnosticReportResult(
        context_path=context_path,
        deterministic_report_path=report_path,
        trace_path=trace_path,
    )
