from __future__ import annotations

import json
from typing import Any

from application.agent_context_service import AgentContextBuildResult
from application.dataset_service import DatasetListResult, DatasetExportSequenceResult
from application.diagnostic_service import DiagnosticRunResult, DiagnosticReportResult, DiagnosticRegressionResult
from application.metrics_service import (
    MetricsIngestResult,
    MetricsListRunsResult,
    MetricsShowRunResult,
)
from application.review_service import ReviewCommandResult
from application.runtime_service import RuntimeTaskResult
from application.sandbox_service import SandboxRunResult
from application.sequence_runtime_service import SequenceRuntimeResult
from application.core import AppResult


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_runtime_task_result(result: RuntimeTaskResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    step = result.step_result
    print(f"Decision: {step.safety_result.decision}")
    print(f"Risk Level: {step.safety_result.risk_level}")
    print(f"Executed: {step.executed}")
    print(f"Blocked Reason: {step.blocked_reason}")
    print(f"Episode Dir: {result.episode_dir}")
    print(f"Episode Step Path: {step.episode_step_path}")


def print_review_command_result(result: ReviewCommandResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    safety = result.safety_result
    print(f"Decision: {safety.decision}")
    print(f"Risk Level: {safety.risk_level}")
    print(f"Min Clearance: {safety.min_clearance}")
    print(f"Closest Link: {safety.closest_robot_link}")
    print(f"Closest Obstacle: {safety.closest_obstacle}")
    print(f"Worst Step: {safety.worst_step}")
    print(f"Log Path: {result.log_path or ''}")


def print_sequence_runtime_result(result: SequenceRuntimeResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    print(f"Sequence: {result.sequence_id}")
    print(f"Backend: {result.backend_name}")
    print(f"Device: {result.device_name}")
    print(f"Total Steps: {result.total_steps}")
    print(f"Approved Steps: {result.approved_steps}")
    print(f"Executed Steps: {result.executed_steps}")
    print(f"Blocked Steps: {result.blocked_steps}")
    print(f"Rejected Steps: {result.rejected_steps}")
    print(f"Manual Review Steps: {result.manual_review_steps}")
    print(f"Episode Dir: {result.episode_dir}")


def print_dataset_list_result(result: DatasetListResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    print(f"Adapter: {result.adapter_name}")
    print(f"Source: {result.source}")
    print(f"Sequences ({result.to_dict()['count']}):")
    for sid in result.sequence_ids:
        print(f"  - {sid}")


def print_dataset_export_result(result: DatasetExportSequenceResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    print(f"Adapter: {result.adapter_name}")
    print(f"Sequence ID: {result.sequence_id}")
    print(f"Exported Path: {result.exported_path}")


def print_sandbox_run_result(result: SandboxRunResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    runtime = result.sequence_runtime_result
    print(f"Sequence: {runtime.sequence_id}")
    print(f"Backend: {runtime.backend_name}")
    print(f"Total Steps: {runtime.total_steps}")
    print(f"Approved Steps: {runtime.approved_steps}")
    print(f"Executed Steps: {runtime.executed_steps}")
    print(f"Blocked Steps: {runtime.blocked_steps}")
    print(f"Episode Dir: {runtime.episode_dir}")
    print(f"Episode Summary: {result.episode_summary_path}")
    print(f"Clearance Curve: {result.clearance_curve_path}")
    print(f"Trajectory Overview: {result.trajectory_overview_path}")


def print_metrics_ingest_result(result: MetricsIngestResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    d = result.to_dict()
    print(f"Episode ID: {d.get('episode_id', '?')}")
    print(f"Total Steps: {d.get('total_steps', '?')}")
    print(f"Approved Steps: {d.get('approved_steps', '?')}")
    print(f"Artifact Count: {d.get('artifact_count', '?')}")


def print_metrics_list_runs_result(result: MetricsListRunsResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    d = result.to_dict()
    print(f"Runs ({d['count']}):")
    for run in d["runs"]:
        print(
            f"  {run.get('episode_id', '?'):30s}"
            f" steps={run.get('total_steps', '?'):>2}"
            f"  approved={run.get('approved_steps', '?'):>2}"
            f"  rejected={run.get('rejected_steps', '?'):>2}"
            f"  blocked={run.get('blocked_steps', '?'):>2}"
            f"  manual_review={run.get('manual_review_steps', '?'):>2}"
        )


def print_metrics_show_run_result(result: MetricsShowRunResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    d = result.to_dict()
    run = d.get("run")
    if run is None:
        print("Run not found.")
        return
    print(f"Episode ID: {run.get('episode_id', '?')}")
    print(f"Total Steps: {run.get('total_steps', '?')}")
    print(f"Approved: {run.get('approved_steps', '?')}")
    print(f"Executed: {run.get('executed_steps', '?')}")
    print(f"Blocked: {run.get('blocked_steps', '?')}")
    print(f"Steps ({d['step_count']}):")
    for step in d["steps"]:
        sid = step.get("step_id") or step.get("step_index", "?")
        dec = step.get("decision", "?")
        print(f"  {sid}: {dec}")


def print_agent_context_build_result(result: AgentContextBuildResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    d = result.to_dict()
    print(f"Episode ID: {d.get('episode_id', '?')}")
    print(f"Total Steps: {d.get('total_steps', '?')}")
    print(f"Critical Steps: {d.get('critical_step_count', '?')}")
    print(f"JSON: {d.get('json_path', 'N/A')}")
    print(f"Markdown: {d.get('markdown_path', 'N/A')}")


def print_diagnostic_run_result(result: DiagnosticRunResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    d = result.to_dict()
    print(f"Episode ID: {d.get('episode_id', '?')}")
    print(f"Total Steps: {d.get('total_steps', '?')}")
    print(f"Critical Steps: {d.get('critical_step_count', '?')}")
    print(f"Context: {d.get('context_path', 'N/A')}")
    print(f"Deterministic Report: {d.get('deterministic_report_path', 'N/A')}")
    if d.get("agent_report_path"):
        print(f"Agent Report: {d['agent_report_path']}")
    print(f"Trace: {d.get('trace_path', 'N/A')}")
    if d.get("evidence_manifest_path"):
        print(f"Evidence Manifest: {d['evidence_manifest_path']}")
    if d.get("safety_violations"):
        print(f"Safety Violations: {d['safety_violations']}")


def print_diagnostic_report_result(result: DiagnosticReportResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    d = result.to_dict()
    print(f"Context: {d.get('context_path', 'N/A')}")
    print(f"Deterministic Report: {d.get('deterministic_report_path', 'N/A')}")
    print(f"Trace: {d.get('trace_path', 'N/A')}")
    if d.get("evidence_manifest_path"):
        print(f"Evidence Manifest: {d['evidence_manifest_path']}")


def print_diagnostic_regression_result(result: DiagnosticRegressionResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    d = result.to_dict()
    print(f"Diagnostic Regression")
    print(f"Total Cases: {d.get('total_cases', 0)}")
    print(f"Passed Cases: {d.get('passed_cases', 0)}")
    print(f"Failed Cases: {d.get('failed_cases', 0)}")
    print(f"Summary: {d.get('summary_path', 'N/A')}")
    print("Cases:")
    for case in d.get("cases", []):
        status = "PASS" if case.get("ok") else "FAIL"
        ep = case.get("episode_id") or ""
        extra = ""
        cp = case.get("contract_passed")
        if cp is not None:
            extra = f" pipeline={case.get('pipeline_passed')} evidence={case.get('evidence_complete')} contract={cp}"
        if case.get("errors"):
            print(f"  - {case['case_id']}: {status} errors={case['errors']}{extra}")
        else:
            print(f"  - {case['case_id']}: {status} episode={ep}{extra}")


def print_app_result(result: AppResult, *, as_json: bool) -> None:
    """Print an ``AppResult`` as JSON or structured text."""
    if as_json:
        print_json(result.to_dict())
        return

    d = result.to_dict()
    print(f"Mode: {d.get('mode', '?')}")
    print(f"OK: {d.get('ok', '?')}")
    for art in d.get("artifacts", []):
        print(f"  Artifact ({art.get('kind', '?')}): {art.get('path', '?')}")
