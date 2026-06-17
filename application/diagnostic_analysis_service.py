from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from diagnostic_runtime.analysis.fake_analyst import run_fake_diagnostic_analyst
from .core import AppResult, ArtifactRef


@dataclass(frozen=True)
class DiagnosticAnalysisRequest:
    """Request to run diagnostic analysis on an episode's evidence."""

    context_path: Path
    evidence_manifest_path: Path
    output_dir: Path = Path("output_reports/diagnostic_analysis")
    deterministic_report_path: Path | None = None
    provider: str = "fake"


@dataclass(frozen=True)
class DiagnosticAnalysisResult:
    """Result of a diagnostic analysis run."""

    context_path: Path
    evidence_manifest_path: Path
    deterministic_report_path: Path | None
    analysis_path: Path
    provider: str = "fake"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "diagnostic_analysis_result.v1",
            "context_path": str(self.context_path),
            "evidence_manifest_path": str(self.evidence_manifest_path),
            "deterministic_report_path": str(self.deterministic_report_path) if self.deterministic_report_path else None,
            "analysis_path": str(self.analysis_path),
            "provider": self.provider,
        }

    def to_app_result(self) -> AppResult:
        return AppResult(
            ok=True,
            mode="diagnostic_analysis",
            data=self.to_dict(),
            artifacts=(
                ArtifactRef(
                    kind="llm_diagnostic_analysis",
                    path=self.analysis_path,
                    description="Structured diagnostic analysis JSON",
                ),
            ),
        )


def run_diagnostic_analysis(request: DiagnosticAnalysisRequest) -> DiagnosticAnalysisResult:
    """Run the diagnostic analysis pipeline: load evidence -> fake analyst -> write JSON.

    Args:
        request: The analysis request with paths and provider.

    Returns:
        A ``DiagnosticAnalysisResult`` with the path to the written analysis JSON.

    Raises:
        FileNotFoundError: If any required input path does not exist.
        ValueError: If *provider* is not ``"fake"``.
    """
    context_path = Path(request.context_path)
    if not context_path.exists():
        raise FileNotFoundError(f"diagnostic context not found: {context_path}")

    manifest_path = Path(request.evidence_manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"evidence manifest not found: {manifest_path}")

    provider = request.provider
    if provider != "fake":
        raise ValueError(f"unsupported diagnostic analysis provider: '{provider}'")

    # Read inputs
    context = json.loads(context_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    deterministic_report: str | None = None
    if request.deterministic_report_path is not None:
        report_path = Path(request.deterministic_report_path)
        if not report_path.exists():
            raise FileNotFoundError(f"deterministic report not found: {report_path}")
        deterministic_report = report_path.read_text(encoding="utf-8")

    # Run fake analyst
    analysis = run_fake_diagnostic_analyst(
        context=context,
        manifest=manifest,
        deterministic_report=deterministic_report,
    )

    # Write output
    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    analysis_path = output_dir / "llm_diagnostic_analysis.json"
    analysis_path.write_text(
        json.dumps(analysis.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return DiagnosticAnalysisResult(
        context_path=context_path,
        evidence_manifest_path=manifest_path,
        deterministic_report_path=Path(request.deterministic_report_path) if request.deterministic_report_path else None,
        analysis_path=analysis_path,
        provider=provider,
    )
