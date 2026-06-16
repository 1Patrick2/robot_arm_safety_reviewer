from __future__ import annotations

import argparse
from pathlib import Path

from application.diagnostic_service import (
    DiagnosticReportRequest,
    DiagnosticRunRequest,
    run_diagnostic,
    run_diagnostic_report,
)
from cli.output import print_diagnostic_run_result, print_diagnostic_report_result


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
