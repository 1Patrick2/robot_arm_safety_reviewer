from __future__ import annotations

import argparse
from pathlib import Path

from application.runtime_service import RuntimeTaskRequest, run_runtime_task
from cli.output import print_runtime_task_result


def register_runtime_commands(subparsers) -> None:
    runtime_parser = subparsers.add_parser("runtime", help="Runtime safety interposer commands")
    runtime_subparsers = runtime_parser.add_subparsers(dest="runtime_command", required=True)

    run_parser = runtime_subparsers.add_parser("run", help="Run one runtime task")
    run_parser.add_argument("--task", required=True, help="Benchmark task directory containing scene.json/command.json")
    run_parser.add_argument("--backend", default="mock", choices=("mock", "pybullet"))
    run_parser.add_argument("--episode-root", default="output_reports/runtime_demo")
    run_parser.add_argument("--json", action="store_true")
    run_parser.set_defaults(handler=handle_runtime_run)


def handle_runtime_run(args: argparse.Namespace) -> None:
    result = run_runtime_task(
        RuntimeTaskRequest(
            task_dir=Path(args.task),
            backend_name=args.backend,
            episode_root=Path(args.episode_root),
        )
    )
    print_runtime_task_result(result, as_json=args.json)

