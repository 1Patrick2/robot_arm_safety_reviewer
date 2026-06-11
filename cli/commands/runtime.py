from __future__ import annotations

import argparse
import json
from pathlib import Path

from application.runtime_service import RuntimeTaskRequest, run_runtime_task


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
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    step = result.step_result
    print(f"Decision: {step.safety_result.decision}")
    print(f"Risk Level: {step.safety_result.risk_level}")
    print(f"Executed: {step.executed}")
    print(f"Blocked Reason: {step.blocked_reason}")
    print(f"Episode Dir: {result.episode_dir}")
    print(f"Episode Step Path: {step.episode_step_path}")

