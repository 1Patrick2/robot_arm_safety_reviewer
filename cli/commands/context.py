from __future__ import annotations

import argparse
from pathlib import Path

from application.agent_context_service import AgentContextBuildRequest, build_agent_context
from cli.output import print_agent_context_build_result


def register_context_commands(subparsers) -> None:
    ctx_parser = subparsers.add_parser("context", help="Diagnostic agent context commands")
    ctx_subparsers = ctx_parser.add_subparsers(dest="context_command", required=True)

    build_parser = ctx_subparsers.add_parser("build", help="Build a diagnostic context package for an episode")
    build_parser.add_argument("--db", default="output_reports/runtime_metrics/runtime_metrics.db", help="Path to the metrics SQLite database")
    build_parser.add_argument("--episode-id", required=True, help="Episode ID to build context for")
    build_parser.add_argument("--output-dir", required=True, help="Output directory for context files")
    build_parser.add_argument("--max-steps", type=int, default=10, help="Maximum critical steps in context")
    build_parser.add_argument("--json", action="store_true")
    build_parser.set_defaults(handler=handle_context_build)


def handle_context_build(args: argparse.Namespace) -> None:
    result = build_agent_context(
        AgentContextBuildRequest(
            episode_id=args.episode_id,
            db_path=Path(args.db),
            output_dir=Path(args.output_dir),
            max_steps=args.max_steps,
        )
    )
    print_agent_context_build_result(result, as_json=args.json)
