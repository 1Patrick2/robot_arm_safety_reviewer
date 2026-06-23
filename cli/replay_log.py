"""Replay a robot arm safety execution log."""

from __future__ import annotations

import argparse
import json

from application.gateway.replay import replay_log


def main() -> None:
    """Parse args, replay the safety log, and print consistency checks."""
    parser = argparse.ArgumentParser(description="Replay a robot arm safety log and check consistency.")
    parser.add_argument("--log", required=True, help="Path to execution log JSON")
    parser.add_argument("--json", action="store_true", help="Print full replay result JSON")
    args = parser.parse_args()

    result = replay_log(args.log)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"Log ID: {result['log_id']}")
    print(f"Consistent: {result['consistent']}")
    for check, passed in result["checks"].items():
        print(f"- {check}: {passed}")


if __name__ == "__main__":
    main()
