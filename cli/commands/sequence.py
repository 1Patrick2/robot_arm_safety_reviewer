from __future__ import annotations

import argparse
from pathlib import Path

from application.sequence_runtime_service import SequenceRuntimeRequest, run_sequence_runtime
from cli.output import print_sequence_runtime_result


def register_sequence_commands(subparsers) -> None:
    sequence_parser = subparsers.add_parser("sequence", help="Policy action sequence runtime commands")
    sequence_subparsers = sequence_parser.add_subparsers(dest="sequence_command", required=True)

    run_parser = sequence_subparsers.add_parser("run", help="Run a policy action sequence")
    run_parser.add_argument("--sequence", required=True, help="PolicyActionSequence JSON file")
    run_parser.add_argument("--scene", required=True, help="Scene JSON file used for safety review")
    run_parser.add_argument("--backend", default="mock", choices=("mock", "pybullet"))
    run_parser.add_argument("--device", default="mock_realman", choices=("mock_realman",))
    run_parser.add_argument("--episode-root", default="output_reports/sequence_runtime")
    run_parser.add_argument("--continue-on-reject", action="store_true")
    run_parser.add_argument("--json", action="store_true")
    run_parser.set_defaults(handler=handle_sequence_run)


def handle_sequence_run(args: argparse.Namespace) -> None:
    result = run_sequence_runtime(
        SequenceRuntimeRequest(
            sequence_path=Path(args.sequence),
            scene_path=Path(args.scene),
            backend_name=args.backend,
            device_name=args.device,
            episode_root=Path(args.episode_root),
            stop_on_reject=not args.continue_on_reject,
        )
    )
    print_sequence_runtime_result(result, as_json=args.json)
