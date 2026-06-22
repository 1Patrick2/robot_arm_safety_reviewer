from __future__ import annotations

from pathlib import Path

from ..tools.context_tools import load_diagnostic_context
from ..report.deterministic import build_diagnostic_report
from ..agent.runner import run_diagnostic_agent
from ..guardrails.safety_check import check_agent_report

from .models import DiagnosticRuntimeRequest, DiagnosticRuntimeResult
from .trace import write_runtime_trace


def run_diagnostic_runtime(request: DiagnosticRuntimeRequest) -> DiagnosticRuntimeResult:
    """Run the full diagnostic runtime pipeline:
    load context → build deterministic report → optionally run agent → write trace.
    """
    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load diagnostic context
    bundle = load_diagnostic_context(request.context_path)

    # 2. Build deterministic diagnostic report
    report_md = build_diagnostic_report(bundle)
    report_path = output_dir / "diagnostic_report.md"
    report_path.write_text(report_md, encoding="utf-8")

    # 3. Optionally run diagnostic agent
    agent_report_path: Path | None = None
    safety_violations: list[str] = []
    if request.run_agent:
        agent_result = run_diagnostic_agent(
            context_path=request.context_path,
            output_dir=output_dir / "agent",
            provider=request.provider,
        )
        agent_report_path = Path(agent_result["report_path"])
        safety_violations = agent_result.get("safety_violations", [])

    # 4. Build result
    trace_path = output_dir / "diagnostic_runtime_trace.json"
    result = DiagnosticRuntimeResult(
        context_path=Path(request.context_path),
        deterministic_report_path=report_path,
        agent_report_path=agent_report_path,
        trace_path=trace_path,
        safety_violations=tuple(safety_violations),
    )

    # 5. Write trace
    write_runtime_trace(result)

    return result
