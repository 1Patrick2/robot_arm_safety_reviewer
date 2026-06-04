"""Review a command and simulate execution only when approved."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gateway.safety_gate import execute_if_safe
from robots.mock_realman_6dof import MockRealMan6DoFAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description="Review and conditionally simulate a robot arm joint move.")
    parser.add_argument("--scene", required=True, help="Path to scene.json")
    parser.add_argument("--command", required=True, help="Path to command.json")
    parser.add_argument("--robot", default="mock_realman", choices=["mock_realman"], help="Robot adapter to use")
    parser.add_argument("--log-dir", default="logs", help="Directory for execution logs")
    parser.add_argument("--json", action="store_true", help="Print full execution log JSON")
    args = parser.parse_args()

    adapter = _build_adapter(args.robot)
    outcome = execute_if_safe(args.scene, args.command, robot_adapter=adapter, log_dir=args.log_dir)
    result = outcome.safety_result
    execution = outcome.execution_log["execution"]
    if args.json:
        print(json.dumps(outcome.execution_log, ensure_ascii=False, indent=2))
        return

    print(f"Decision: {result.decision}")
    print(f"Risk Level: {result.risk_level}")
    print(f"Executed: {execution['executed']}")
    print(f"Execution Reason: {execution['reason']}")
    print(f"Min Clearance: {result.min_clearance}")
    print(f"Closest Link: {result.closest_robot_link}")
    print(f"Closest Obstacle: {result.closest_obstacle}")
    if result.violations:
        print("Violations:")
        for violation in result.violations:
            print(f"- {violation.type}: {violation.message}")
    if result.evidence:
        print("Evidence:")
        for item in result.evidence:
            print(f"- {item}")
    print(f"Log Path: {Path(outcome.log_path) if outcome.log_path else ''}")


def _build_adapter(name: str):
    if name == "mock_realman":
        return MockRealMan6DoFAdapter()
    raise ValueError(f"unsupported robot adapter: {name}")


if __name__ == "__main__":
    main()
