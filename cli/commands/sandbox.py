from __future__ import annotations

import argparse
from pathlib import Path

from application.sandbox_service import SandboxRunRequest, run_sandbox
from cli.output import print_sandbox_run_result


def register_sandbox_commands(subparsers) -> None:
    sandbox_parser = subparsers.add_parser("sandbox", help="Visual sandbox commands")
    sandbox_subparsers = sandbox_parser.add_subparsers(dest="sandbox_command", required=True)

    run_parser = sandbox_subparsers.add_parser("run", help="Run a sequence through the sandbox with visual artifacts")
    run_parser.add_argument("--sequence", required=True, help="PolicyActionSequence JSON file")
    run_parser.add_argument("--scene", required=True, help="Scene JSON file used for safety review")
    run_parser.add_argument("--backend", default="mock", choices=("mock", "pybullet"))
    run_parser.add_argument("--device", default="mock_realman", choices=("mock_realman",))
    run_parser.add_argument("--output-root", default="output_reports/sandbox")
    run_parser.add_argument("--continue-on-block", action="store_true")
    run_parser.add_argument("--json", action="store_true")
    run_parser.set_defaults(handler=handle_sandbox_run)


def handle_sandbox_run(args: argparse.Namespace) -> None:
    result = run_sandbox(
        SandboxRunRequest(
            sequence_path=Path(args.sequence),
            scene_path=Path(args.scene),
            backend_name=args.backend,
            device_name=args.device,
            output_root=Path(args.output_root),
            stop_on_block=not args.continue_on_block,
        )
    )
    print_sandbox_run_result(result, as_json=args.json)
