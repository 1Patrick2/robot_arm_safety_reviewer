from __future__ import annotations

import argparse
import json
from pathlib import Path

from application.review_service import ReviewCommandRequest, review_command


def register_review_commands(subparsers) -> None:
    review_parser = subparsers.add_parser("review", help="Review one scene/command pair")
    review_parser.add_argument("--scene", required=True, help="Path to scene.json")
    review_parser.add_argument("--command", required=True, help="Path to command.json")
    review_parser.add_argument("--backend", default="mock", choices=("mock", "pybullet"))
    review_parser.add_argument("--log-dir", default="logs")
    review_parser.add_argument("--json", action="store_true")
    review_parser.set_defaults(handler=handle_review)


def handle_review(args: argparse.Namespace) -> None:
    result = review_command(
        ReviewCommandRequest(
            scene_path=Path(args.scene),
            command_path=Path(args.command),
            backend_name=args.backend,
            log_dir=Path(args.log_dir),
        )
    )
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    safety = result.safety_result
    print(f"Decision: {safety.decision}")
    print(f"Risk Level: {safety.risk_level}")
    print(f"Min Clearance: {safety.min_clearance}")
    print(f"Closest Link: {safety.closest_robot_link}")
    print(f"Closest Obstacle: {safety.closest_obstacle}")
    print(f"Worst Step: {safety.worst_step}")
    print(f"Log Path: {result.log_path or ''}")
