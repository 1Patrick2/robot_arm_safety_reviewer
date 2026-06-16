from __future__ import annotations

import argparse
from pathlib import Path

from application.diagnostic_service import DiagnosticRunRequest, run_diagnostic
from cli.output import print_diagnostic_run_result


def register_diagnostic_commands(subparsers) -> None:
    diag_parser = subparsers.add_parser("diagnostic", help="Diagnostic runtime commands")
    diag_subparsers = diag_parser.add_subparsers(dest="diagnostic_command", required=True)

    run_parser = diag_subparsers.add_parser("run", help="Run the full diagnostic pipeline for an episode")
    run_parser.add_argument("--episode-id", required=True, help="Episode ID to diagnose")
    run_parser.add_argument("--db", default="output_reports/runtime_metrics/runtime_metrics.db", help="Path to the metrics SQLite database")
    run_parser.add_argument("--output-dir", default="output_reports/diagnostics", help="Output directory for diagnostic artifacts")
    run_parser.add_argument("--provider", default="fake", choices=("fake", "deepseek"), help="Diagnostic agent provider")
    run_parser.add_argument("--max-steps", type=int, default=10, help="Maximum critical steps in context")
    run_parser.add_argument("--run-agent", action="store_true", help="Run the diagnostic agent after generating the report")
    run_parser.add_argument("--json", action="store_true")
    run_parser.set_defaults(handler=handle_diagnostic_run)


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
