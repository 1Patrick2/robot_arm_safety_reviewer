"""Subcommand: ``review`` -- review one scene/command pair.

Registers the ``review`` subcommand and provides a handler that invokes the
review service and prints the result.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from application.review_service import ReviewCommandRequest, review_command
from cli.output import print_review_command_result


def register_review_commands(subparsers) -> None:
    """Register the ``review`` subcommand."""
    review_parser = subparsers.add_parser("review", help="Review one scene/command pair")
    review_parser.add_argument("--scene", required=True, help="Path to scene.json")
    review_parser.add_argument("--command", required=True, help="Path to command.json")
    review_parser.add_argument("--backend", default="mock", choices=("mock", "pybullet"))
    review_parser.add_argument("--log-dir", default="logs")
    review_parser.add_argument("--json", action="store_true")
    review_parser.set_defaults(handler=handle_review)


def handle_review(args: argparse.Namespace) -> None:
    """Run the safety review for a scene/command pair and print the result."""
    result = review_command(
        ReviewCommandRequest(
            scene_path=Path(args.scene),
            command_path=Path(args.command),
            backend_name=args.backend,
            log_dir=Path(args.log_dir),
        )
    )
    print_review_command_result(result, as_json=args.json)
