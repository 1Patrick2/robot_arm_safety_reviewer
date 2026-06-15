from __future__ import annotations

import argparse

from .commands.review import register_review_commands
from .commands.runtime import register_runtime_commands
from .commands.sequence import register_sequence_commands


def main() -> None:
    parser = argparse.ArgumentParser(description="Robot arm safety reviewer unified CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_runtime_commands(subparsers)
    register_review_commands(subparsers)
    register_sequence_commands(subparsers)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
