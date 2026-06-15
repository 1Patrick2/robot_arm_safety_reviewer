from __future__ import annotations

import argparse
from pathlib import Path

from application.metrics_service import (
    MetricsIngestRequest,
    MetricsListRunsRequest,
    MetricsShowRunRequest,
    metrics_ingest_episode,
    metrics_list_runs,
    metrics_show_run,
)
from cli.output import print_metrics_ingest_result, print_metrics_list_runs_result, print_metrics_show_run_result


def register_metrics_commands(subparsers) -> None:
    metrics_parser = subparsers.add_parser("metrics", help="Runtime metrics database commands")
    metrics_subparsers = metrics_parser.add_subparsers(dest="metrics_command", required=True)

    # metrics ingest
    ingest_parser = metrics_subparsers.add_parser("ingest", help="Ingest an episode into the metrics database")
    ingest_parser.add_argument("--episode-dir", required=True, help="Path to the episode directory")
    ingest_parser.add_argument("--db", default="output_reports/runtime_metrics/runtime_metrics.db", help="Path to the SQLite database")
    ingest_parser.add_argument("--json", action="store_true")
    ingest_parser.set_defaults(handler=handle_metrics_ingest)

    # metrics list-runs
    list_parser = metrics_subparsers.add_parser("list-runs", help="List ingested runs")
    list_parser.add_argument("--db", default="output_reports/runtime_metrics/runtime_metrics.db", help="Path to the SQLite database")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum number of runs to return")
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=handle_metrics_list_runs)

    # metrics show-run
    show_parser = metrics_subparsers.add_parser("show-run", help="Show details for a single run")
    show_parser.add_argument("--db", default="output_reports/runtime_metrics/runtime_metrics.db", help="Path to the SQLite database")
    show_parser.add_argument("--episode-id", required=True, help="Episode ID to show")
    show_parser.add_argument("--json", action="store_true")
    show_parser.set_defaults(handler=handle_metrics_show_run)


def handle_metrics_ingest(args: argparse.Namespace) -> None:
    result = metrics_ingest_episode(
        MetricsIngestRequest(
            episode_dir=Path(args.episode_dir),
            db_path=Path(args.db),
        )
    )
    print_metrics_ingest_result(result, as_json=args.json)


def handle_metrics_list_runs(args: argparse.Namespace) -> None:
    result = metrics_list_runs(
        MetricsListRunsRequest(
            db_path=Path(args.db),
            limit=args.limit,
        )
    )
    print_metrics_list_runs_result(result, as_json=args.json)


def handle_metrics_show_run(args: argparse.Namespace) -> None:
    result = metrics_show_run(
        MetricsShowRunRequest(
            episode_id=args.episode_id,
            db_path=Path(args.db),
        )
    )
    print_metrics_show_run_result(result, as_json=args.json)
