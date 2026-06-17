from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agent_context_service import build_agent_context, AgentContextBuildRequest
from diagnostic_runtime.runtime.models import DiagnosticRuntimeRequest
from diagnostic_runtime.runtime.runner import run_diagnostic_runtime
from reports.evidence_manifest import build_evidence_manifest, write_evidence_manifest
from .diagnostic_contracts import build_actual_summary, load_expected_contract, validate_expected_contract
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
    evidence_manifest_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.context.get("episode_id"),
            "total_steps": self.context.get("total_steps"),
            "critical_step_count": len(self.context.get("critical_steps", [])),
            "context_path": str(self.context_path),
            "deterministic_report_path": str(self.deterministic_report_path),
            "agent_report_path": str(self.agent_report_path) if self.agent_report_path else None,
            "trace_path": str(self.trace_path),
            "evidence_manifest_path": str(self.evidence_manifest_path),
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
        artifacts.extend([
            ArtifactRef(kind="diagnostic_trace", path=self.trace_path, description="Diagnostic runtime trace"),
            ArtifactRef(kind="evidence_manifest", path=self.evidence_manifest_path, description="Evidence manifest JSON"),
        ])
        return AppResult(
            ok=len(self.safety_violations) == 0,
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

    # 3. Build evidence manifest
    manifest = build_evidence_manifest(
        context_path=context_path,
        deterministic_report_path=runtime_result.deterministic_report_path,
        agent_report_path=runtime_result.agent_report_path,
        trace_path=runtime_result.trace_path,
    )
    manifest_path = episode_dir / "evidence_manifest.json"
    write_evidence_manifest(manifest, manifest_path)

    return DiagnosticRunResult(
        context_path=context_path,
        context=context.to_dict(),
        deterministic_report_path=runtime_result.deterministic_report_path,
        agent_report_path=runtime_result.agent_report_path,
        trace_path=runtime_result.trace_path,
        safety_violations=runtime_result.safety_violations,
        evidence_manifest_path=manifest_path,
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
    evidence_manifest_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_path": str(self.context_path),
            "deterministic_report_path": str(self.deterministic_report_path),
            "trace_path": str(self.trace_path),
            "evidence_manifest_path": str(self.evidence_manifest_path),
        }

    def to_app_result(self) -> AppResult:
        return AppResult(
            ok=True,
            mode="diagnostic_report",
            data=self.to_dict(),
            artifacts=(
                ArtifactRef(kind="deterministic_report", path=self.deterministic_report_path, description="Deterministic diagnostic report"),
                ArtifactRef(kind="diagnostic_trace", path=self.trace_path, description="Diagnostic runtime trace"),
                ArtifactRef(kind="evidence_manifest", path=self.evidence_manifest_path, description="Evidence manifest JSON"),
            ),
        )


def run_diagnostic_report(request: DiagnosticReportRequest) -> DiagnosticReportResult:
    """Generate a deterministic diagnostic report and trace + manifest from an existing context file.
    Does not query the metrics DB or run an agent."""
    context_path = Path(request.context_path)
    if not context_path.exists():
        raise FileNotFoundError(f"context not found: {context_path}")

    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Reuse the diagnostic runtime pipeline (load context → report → trace)
    runtime_result = run_diagnostic_runtime(
        DiagnosticRuntimeRequest(
            context_path=context_path,
            output_dir=output_dir,
            provider="fake",
            run_agent=False,
        )
    )

    # Build evidence manifest
    manifest = build_evidence_manifest(
        context_path=context_path,
        deterministic_report_path=runtime_result.deterministic_report_path,
        trace_path=runtime_result.trace_path,
    )
    manifest_path = output_dir / "evidence_manifest.json"
    write_evidence_manifest(manifest, manifest_path)

    return DiagnosticReportResult(
        context_path=context_path,
        deterministic_report_path=runtime_result.deterministic_report_path,
        trace_path=runtime_result.trace_path,
        evidence_manifest_path=manifest_path,
    )


# ── diagnostic regression ────────────────────────────────────────────


@dataclass(frozen=True)
class DiagnosticRegressionCase:
    case_id: str
    sequence_path: Path
    scene_path: Path
    expected_contract_path: Path | None = None


@dataclass(frozen=True)
class DiagnosticRegressionRequest:
    cases: tuple[DiagnosticRegressionCase, ...]
    output_dir: Path = Path("output_reports/diagnostics_regression")
    backend_name: str = "mock"
    provider: str = "fake"
    run_agent: bool = False
    max_steps: int = 10


@dataclass(frozen=True)
class DiagnosticRegressionCaseResult:
    case_id: str
    ok: bool
    episode_id: str | None
    diagnostic_output_dir: Path
    context_path: Path | None
    deterministic_report_path: Path | None
    trace_path: Path | None
    evidence_manifest_path: Path | None
    agent_report_path: Path | None
    safety_violations: tuple[str, ...]
    errors: tuple[str, ...]
    pipeline_passed: bool = True
    evidence_complete: bool = True
    contract_passed: bool | None = None
    expected: dict[str, Any] | None = None
    actual: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "ok": self.ok,
            "episode_id": self.episode_id,
            "diagnostic_output_dir": str(self.diagnostic_output_dir),
            "context_path": str(self.context_path) if self.context_path else None,
            "deterministic_report_path": str(self.deterministic_report_path) if self.deterministic_report_path else None,
            "trace_path": str(self.trace_path) if self.trace_path else None,
            "evidence_manifest_path": str(self.evidence_manifest_path) if self.evidence_manifest_path else None,
            "agent_report_path": str(self.agent_report_path) if self.agent_report_path else None,
            "safety_violations": list(self.safety_violations),
            "errors": list(self.errors),
            "pipeline_passed": self.pipeline_passed,
            "evidence_complete": self.evidence_complete,
            "contract_passed": self.contract_passed,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass(frozen=True)
class DiagnosticRegressionResult:
    total_cases: int
    passed_cases: int
    failed_cases: int
    case_results: tuple[DiagnosticRegressionCaseResult, ...]
    summary_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "diagnostic_regression.v1",
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "summary_path": str(self.summary_path),
            "cases": [r.to_dict() for r in self.case_results],
        }

    def to_app_result(self) -> AppResult:
        return AppResult(
            ok=self.failed_cases == 0,
            mode="diagnostic_regression",
            data=self.to_dict(),
            artifacts=(ArtifactRef(kind="regression_summary", path=self.summary_path, description="Regression summary JSON"),),
        )


def run_diagnostic_regression(request: DiagnosticRegressionRequest) -> DiagnosticRegressionResult:
    """Run a diagnostic regression over a set of fixed cases.

    For each case: run sandbox -> metrics DB -> diagnostic run -> evidence manifest.
    Aggregates results into a summary JSON.
    """
    from application.sandbox_service import SandboxRunRequest, run_sandbox

    if not request.cases:
        raise ValueError("diagnostic regression requires at least one case")

    root_dir = Path(request.output_dir)
    root_dir.mkdir(parents=True, exist_ok=True)

    case_results: list[DiagnosticRegressionCaseResult] = []

    for case in request.cases:
        case_output = root_dir / case.case_id
        case_output.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Run sandbox with metrics-db
            sandbox_result = run_sandbox(
                SandboxRunRequest(
                    sequence_path=case.sequence_path,
                    scene_path=case.scene_path,
                    backend_name=request.backend_name,
                    output_root=case_output / "sandbox",
                    metrics_db=case_output / "runtime_metrics.db",
                )
            )
            episode_id = sandbox_result.sequence_runtime_result.episode_dir.name

            # 2. Run full diagnostic pipeline
            diag_result = run_diagnostic(
                DiagnosticRunRequest(
                    episode_id=episode_id,
                    db_path=case_output / "runtime_metrics.db",
                    output_dir=case_output / "diagnostics",
                    provider=request.provider,
                    max_steps=request.max_steps,
                    run_agent=request.run_agent,
                )
            )

            # Check artifact completeness
            case_errors: list[str] = []
            required_paths = {
                "context_path": diag_result.context_path,
                "deterministic_report_path": diag_result.deterministic_report_path,
                "trace_path": diag_result.trace_path,
                "evidence_manifest_path": diag_result.evidence_manifest_path,
            }
            for name, path in required_paths.items():
                if path is None or not path.exists():
                    case_errors.append(f"missing {name}: {path}")

            if request.run_agent:
                if diag_result.agent_report_path is None:
                    case_errors.append("missing agent_report_path: None")
                elif not diag_result.agent_report_path.exists():
                    case_errors.append(f"missing agent_report_path: {diag_result.agent_report_path}")

            if diag_result.safety_violations:
                case_errors.append(f"safety violations: {list(diag_result.safety_violations)}")

            pipeline_passed = True
            evidence_complete = not case_errors
            contract_passed: bool | None = None
            expected: dict[str, Any] | None = None
            actual: dict[str, Any] | None = None

            # Build actual summary and validate expected contract if one exists
            if pipeline_passed and diag_result.evidence_manifest_path.exists():
                manifest = json.loads(
                    diag_result.evidence_manifest_path.read_text(encoding="utf-8")
                )
                actual = build_actual_summary(diag_result.context)
                if case.expected_contract_path is not None and case.expected_contract_path.exists():
                    contract = load_expected_contract(case.expected_contract_path)
                    # Verify case_id matches
                    if contract.case_id != case.case_id:
                        contract_passed = False
                        case_errors.append(
                            f"expected_contract case_id mismatch: expected {case.case_id}, "
                            f"got {contract.case_id}"
                        )
                    else:
                        expected = contract.expected
                        cp, contract_errors = validate_expected_contract(
                            expected=contract.expected,
                            actual=actual,
                            manifest=manifest,
                        )
                        contract_passed = cp
                        case_errors.extend(contract_errors)
                elif case.expected_contract_path is not None:
                    contract_passed = False
                    case_errors.append(f"expected_contract not found: {case.expected_contract_path}")

            ok = pipeline_passed and evidence_complete and not case_errors and (contract_passed is not False)

            case_results.append(DiagnosticRegressionCaseResult(
                case_id=case.case_id,
                ok=ok,
                episode_id=episode_id,
                diagnostic_output_dir=diag_result.deterministic_report_path.parent,
                context_path=diag_result.context_path,
                deterministic_report_path=diag_result.deterministic_report_path,
                trace_path=diag_result.trace_path,
                evidence_manifest_path=diag_result.evidence_manifest_path,
                agent_report_path=diag_result.agent_report_path,
                safety_violations=diag_result.safety_violations,
                errors=tuple(case_errors),
                pipeline_passed=pipeline_passed,
                evidence_complete=evidence_complete,
                contract_passed=contract_passed,
                expected=expected,
                actual=actual,
            ))

        except Exception as exc:
            case_results.append(DiagnosticRegressionCaseResult(
                case_id=case.case_id,
                ok=False,
                episode_id=None,
                diagnostic_output_dir=case_output,
                context_path=None,
                deterministic_report_path=None,
                trace_path=None,
                evidence_manifest_path=None,
                agent_report_path=None,
                safety_violations=(),
                errors=(str(exc),),
                pipeline_passed=False,
                evidence_complete=False,
                contract_passed=None,
                expected=None,
                actual=None,
            ))

    total_cases = len(case_results)
    passed_cases = sum(1 for r in case_results if r.ok)
    failed_cases = total_cases - passed_cases

    # Write summary JSON from result.to_dict() to stay consistent with CLI output
    result = DiagnosticRegressionResult(
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        case_results=tuple(case_results),
        summary_path=root_dir / "regression_summary.json",
    )
    result.summary_path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result
