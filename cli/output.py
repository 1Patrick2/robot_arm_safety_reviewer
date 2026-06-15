from __future__ import annotations

import json
from typing import Any

from application.review_service import ReviewCommandResult
from application.runtime_service import RuntimeTaskResult
from application.sequence_runtime_service import SequenceRuntimeResult


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_runtime_task_result(result: RuntimeTaskResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    step = result.step_result
    print(f"Decision: {step.safety_result.decision}")
    print(f"Risk Level: {step.safety_result.risk_level}")
    print(f"Executed: {step.executed}")
    print(f"Blocked Reason: {step.blocked_reason}")
    print(f"Episode Dir: {result.episode_dir}")
    print(f"Episode Step Path: {step.episode_step_path}")


def print_review_command_result(result: ReviewCommandResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    safety = result.safety_result
    print(f"Decision: {safety.decision}")
    print(f"Risk Level: {safety.risk_level}")
    print(f"Min Clearance: {safety.min_clearance}")
    print(f"Closest Link: {safety.closest_robot_link}")
    print(f"Closest Obstacle: {safety.closest_obstacle}")
    print(f"Worst Step: {safety.worst_step}")
    print(f"Log Path: {result.log_path or ''}")


def print_sequence_runtime_result(result: SequenceRuntimeResult, *, as_json: bool) -> None:
    if as_json:
        print_json(result.to_dict())
        return

    print(f"Sequence: {result.sequence_id}")
    print(f"Backend: {result.backend_name}")
    print(f"Device: {result.device_name}")
    print(f"Total Steps: {result.total_steps}")
    print(f"Approved Steps: {result.approved_steps}")
    print(f"Executed Steps: {result.executed_steps}")
    print(f"Blocked Steps: {result.blocked_steps}")
    print(f"Rejected Steps: {result.rejected_steps}")
    print(f"Manual Review Steps: {result.manual_review_steps}")
    print(f"Episode Dir: {result.episode_dir}")
