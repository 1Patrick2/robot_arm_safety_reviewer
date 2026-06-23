from __future__ import annotations

import argparse
from pathlib import Path

from application.diagnostic_service import (
    DiagnosticRegressionCase,
    DiagnosticRegressionRequest,
    DiagnosticReportRequest,
    DiagnosticRunRequest,
    run_diagnostic,
    run_diagnostic_report,
    run_diagnostic_regression,
)
from application.diagnostic_analysis_service import DiagnosticAnalysisRequest, run_diagnostic_analysis
from cli.output import print_diagnostic_run_result, print_diagnostic_report_result, print_diagnostic_regression_result, print_app_result

SAMPLES = Path(__file__).resolve().parents[2] / "bench" / "samples" / "policy_sequences"
BENCH = Path(__file__).resolve().parents[2] / "bench" / "sim_robot_arm"
LEVEL2 = Path(__file__).resolve().parents[2] / "bench" / "level2_safety_scenarios"

DEFAULT_REGRESSION_CASES = (
    DiagnosticRegressionCase(
        case_id="simple_safe_sequence",
        sequence_path=SAMPLES / "simple_safe_sequence.json",
        scene_path=BENCH / "simple_joint_move_001" / "scene.json",
    ),
)

_LEVEL2_CASE_IDS = (
    "near_threshold_clearance_sequence",
    "midpoint_collision_sequence",
    "mixed_decision_sequence",
)


def _build_regression_cases(case_set: str) -> tuple[DiagnosticRegressionCase, ...]:
    """Build the case tuple for a given ``--case-set`` value."""
    if case_set == "smoke":
        return DEFAULT_REGRESSION_CASES

    level2_cases = tuple(
        DiagnosticRegressionCase(
            case_id=cid,
            sequence_path=LEVEL2 / cid / "sequence.json",
            scene_path=LEVEL2 / cid / "scene.json",
            expected_contract_path=LEVEL2 / cid / "expected_contract.json",
        )
        for cid in _LEVEL2_CASE_IDS
    )

    if case_set == "level2":
        return level2_cases

    # case_set == "all"
    return DEFAULT_REGRESSION_CASES + level2_cases


def register_diagnostic_commands(subparsers) -> None:
    diag_parser = subparsers.add_parser("diagnostic", help="Diagnostic runtime commands")
    diag_subparsers = diag_parser.add_subparsers(dest="diagnostic_command", required=True)

    # diagnostic run
    run_parser = diag_subparsers.add_parser("run", help="Run the full diagnostic pipeline for an episode")
    run_parser.add_argument("--episode-id", required=True, help="Episode ID to diagnose")
    run_parser.add_argument("--db", default="output_reports/runtime_metrics/runtime_metrics.db", help="Path to the metrics SQLite database")
    run_parser.add_argument("--output-dir", default="output_reports/diagnostics", help="Root directory for diagnostic artifacts (episode sub-dir created automatically)")
    run_parser.add_argument("--provider", default="fake", choices=("fake", "deepseek"), help="Diagnostic agent provider")
    run_parser.add_argument("--max-steps", type=int, default=10, help="Maximum critical steps in context")
    run_parser.add_argument("--run-agent", action="store_true", help="Run the diagnostic agent after generating the report")
    run_parser.add_argument("--json", action="store_true")
    run_parser.set_defaults(handler=handle_diagnostic_run)

    # diagnostic report (from existing context)
    report_parser = diag_subparsers.add_parser("report", help="Generate deterministic report from an existing diagnostic context")
    report_parser.add_argument("--context", required=True, help="Path to an existing diagnostic_context.json")
    report_parser.add_argument("--output-dir", required=True, help="Output directory for the report and trace")
    report_parser.add_argument("--json", action="store_true")
    report_parser.set_defaults(handler=handle_diagnostic_report)

    # diagnostic regression
    regression_parser = diag_subparsers.add_parser("regression", help="Run diagnostic regression on fixed sample cases")
    regression_parser.add_argument("--case-set", choices=("smoke", "level2", "all"), default="smoke", help="Regression case set to run: smoke, level2, or all.")
    regression_parser.add_argument("--output-dir", default="output_reports/diagnostics_regression", help="Root directory for regression output")
    regression_parser.add_argument("--backend", default="mock", choices=("mock", "pybullet"))
    regression_parser.add_argument("--provider", default="fake", choices=("fake", "deepseek"))
    regression_parser.add_argument("--run-agent", action="store_true")
    regression_parser.add_argument("--max-steps", type=int, default=10)
    regression_parser.add_argument("--json", action="store_true")
    regression_parser.set_defaults(handler=handle_diagnostic_regression)

    # diagnostic analyze
    analyze_parser = diag_subparsers.add_parser("analyze", help="Run diagnostic analysis on an episode using evidence context and manifest")
    analyze_parser.add_argument("--context", required=True, help="Path to diagnostic_context.json")
    analyze_parser.add_argument("--manifest", required=True, help="Path to evidence_manifest.json")
    analyze_parser.add_argument("--report", help="Path to deterministic diagnostic report (optional)")
    analyze_parser.add_argument("--output-dir", default="output_reports/diagnostic_analysis", help="Output directory for the analysis JSON")
    analyze_parser.add_argument("--provider", default="fake", choices=("fake",), help="Analysis provider (only fake supported)")
    analyze_parser.add_argument("--json", action="store_true")
    analyze_parser.set_defaults(handler=handle_diagnostic_analyze)


def handle_diagnostic_run(args: argparse.Namespace) -> None:
    result = run_diagnostic(
        DiagnosticRunRequest(
            episode_id=args.episode_id,
            db_path=Path(args.db),
            output_dir=Path(args.output_dir),
            provider=args.provider,
            max_steps=args.max_steps,
            run_agent=args.run_agent,
        )
    )
    print_diagnostic_run_result(result, as_json=args.json)


def handle_diagnostic_report(args: argparse.Namespace) -> None:
    result = run_diagnostic_report(
        DiagnosticReportRequest(
            context_path=Path(args.context),
            output_dir=Path(args.output_dir),
        )
    )
    print_diagnostic_report_result(result, as_json=args.json)


def handle_diagnostic_regression(args: argparse.Namespace) -> None:
    case_set = args.case_set
    result = run_diagnostic_regression(
        DiagnosticRegressionRequest(
            cases=_build_regression_cases(case_set),
            output_dir=Path(args.output_dir),
            backend_name=args.backend,
            provider=args.provider,
            run_agent=args.run_agent,
            max_steps=args.max_steps,
            stop_on_block=case_set not in {"level2", "all"},
        )
    )
    print_diagnostic_regression_result(result, as_json=args.json)


def handle_diagnostic_analyze(args: argparse.Namespace) -> None:
    result = run_diagnostic_analysis(
        DiagnosticAnalysisRequest(
            context_path=Path(args.context),
            evidence_manifest_path=Path(args.manifest),
            deterministic_report_path=Path(args.report) if args.report else None,
            output_dir=Path(args.output_dir),
            provider=args.provider,
        )
    )
    print_app_result(result.to_app_result(), as_json=args.json)
