"""Entry point for the robot arm safety reviewer unified CLI.

Parses subcommands and dispatches to the appropriate handler registered by each
command module (review, runtime, sequence, sandbox, dataset, context, diagnostic,
metrics).
"""

from __future__ import annotations

import argparse

from .commands.context import register_context_commands
from .commands.dataset import register_dataset_commands
from .commands.diagnostic import register_diagnostic_commands
from .commands.metrics import register_metrics_commands
from .commands.review import register_review_commands
from .commands.runtime import register_runtime_commands
from .commands.sandbox import register_sandbox_commands
from .commands.sequence import register_sequence_commands


def main() -> None:
    """Build the argument parser, register all subcommands, parse args, and dispatch."""
    parser = argparse.ArgumentParser(description="Robot arm safety reviewer unified CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_context_commands(subparsers)
    register_dataset_commands(subparsers)
    register_diagnostic_commands(subparsers)
    register_metrics_commands(subparsers)
    register_runtime_commands(subparsers)
    register_review_commands(subparsers)
    register_sandbox_commands(subparsers)
    register_sequence_commands(subparsers)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
