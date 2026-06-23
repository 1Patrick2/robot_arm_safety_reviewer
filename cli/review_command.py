"""Review a joint-space command and write a replayable safety log."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from application.gateway.safety_gate import review_only


def main() -> None:
    """Parse args, run the safety review, and print results."""
    parser = argparse.ArgumentParser(description="Review a robot arm joint-space command before execution.")
    parser.add_argument("--scene", required=True, help="Path to scene.json")
    parser.add_argument("--command", required=True, help="Path to command.json")
    parser.add_argument(
        "--backend", default="mock", choices=["mock", "pybullet"], help="Simulation backend for safety review"
    )
    parser.add_argument("--log-dir", default="logs", help="Directory for execution logs")
    parser.add_argument("--json", action="store_true", help="Print full SafetyResult JSON")
    args = parser.parse_args()

    outcome = review_only(args.scene, args.command, backend_name=args.backend, log_dir=args.log_dir)
    result = outcome.safety_result
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    print(f"Decision: {result.decision}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Min Clearance: {result.min_clearance}")
    print(f"Closest Link: {result.closest_robot_link}")
    print(f"Closest Obstacle: {result.closest_obstacle}")
    print(f"Worst Step: {result.worst_step}")
    if result.violations:
        print("Violations:")
        for violation in result.violations:
            print(f"- {violation.type}: {violation.message}")
    if result.evidence:
        print("Evidence:")
        for item in result.evidence:
            print(f"- {item}")
    print(f"Log Path: {Path(outcome.log_path) if outcome.log_path else ''}")


if __name__ == "__main__":
    main()
