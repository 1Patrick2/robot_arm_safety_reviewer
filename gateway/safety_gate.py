"""Pre-execution safety gate for joint-space robot commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from robot_safety.evaluator import evaluate_joint_command
from robot_safety.models import JointCommand, SafetyResult, Scene, Violation
from robots.base import RobotAdapter
from robots.mock_realman_6dof import MockRealMan6DoFAdapter

from .execution_logger import build_execution_log, write_execution_log


@dataclass(frozen=True)
class ReviewOutcome:
    safety_result: SafetyResult
    execution_log: dict
    log_path: Path | None


def review_only(
    scene_path: str | Path,
    command_path: str | Path,
    *,
    log_dir: str | Path | None = "logs",
) -> ReviewOutcome:
    """Review a command and write a replayable log without simulated execution."""

    try:
        scene = Scene.from_json(scene_path)
        command = JointCommand.from_json(command_path)
        result = evaluate_joint_command(scene, command)
    except Exception as exc:
        scene, command = _best_effort_context(scene_path, command_path)
        result = _invalid_command_result(scene.scene_id, command.command_id, str(exc))
    payload = build_execution_log(
        scene=scene,
        command=command,
        safety_result=result,
        executed=False,
        reason="review_only",
        mode="review_only",
        scene_path=scene_path,
        command_path=command_path,
    )
    log_path = write_execution_log(payload, log_dir) if log_dir is not None else None
    return ReviewOutcome(safety_result=result, execution_log=payload, log_path=log_path)


def execute_if_safe(
    scene_path: str | Path,
    command_path: str | Path,
    *,
    robot_adapter: RobotAdapter | None = None,
    log_dir: str | Path | None = "logs",
) -> ReviewOutcome:
    """Review a command and simulate execution only when the safety gate approves it."""

    try:
        scene = Scene.from_json(scene_path)
        command = JointCommand.from_json(command_path)
        result = evaluate_joint_command(scene, command)
    except Exception as exc:
        scene, command = _best_effort_context(scene_path, command_path)
        result = _invalid_command_result(scene.scene_id, command.command_id, str(exc))
    adapter_result = None
    executed = False
    reason = _execution_reason(result.decision)
    if result.decision == "approve":
        adapter = robot_adapter or MockRealMan6DoFAdapter(
            robot_id=scene.robot.robot_id,
            initial_joints=command.current_joints,
        )
        try:
            execution = adapter.execute_joint_move(command.target_joints, command.speed)
            adapter_result = execution.to_dict()
            executed = execution.executed
            reason = execution.reason
        except Exception as exc:
            adapter_result = {
                "robot_id": getattr(adapter, "robot_id", scene.robot.robot_id),
                "executed": False,
                "success": False,
                "reason": "adapter_execution_failed",
                "error_message": str(exc),
            }
            executed = False
            reason = "adapter_execution_failed"
    payload = build_execution_log(
        scene=scene,
        command=command,
        safety_result=result,
        executed=executed,
        reason=reason,
        mode="execute_if_safe",
        scene_path=scene_path,
        command_path=command_path,
        adapter_result=adapter_result,
    )
    log_path = write_execution_log(payload, log_dir) if log_dir is not None else None
    return ReviewOutcome(safety_result=result, execution_log=payload, log_path=log_path)


def _execution_reason(decision: str) -> str:
    if decision == "approve":
        return "approved_by_safety_gate"
    if decision == "manual_review":
        return "manual_review_required"
    return "rejected_by_safety_gate"


def _invalid_command_result(scene_id: str, command_id: str, message: str) -> SafetyResult:
    return SafetyResult(
        scene_id=scene_id,
        command_id=command_id,
        decision="reject",
        risk_level="high",
        joint_limits_ok=False,
        trajectory_collision_free=False,
        self_collision_checked=False,
        self_collision_free=None,
        min_clearance=999.0,
        closest_robot_link=None,
        closest_obstacle=None,
        worst_step=None,
        max_joint_delta=0.0,
        violations=(
            Violation(
                type="invalid_command",
                message=message,
            ),
        ),
        evidence=(
            f"Safety gate rejected the command because input validation failed: {message}",
        ),
    )


def _best_effort_context(scene_path: str | Path, command_path: str | Path) -> tuple[Scene, JointCommand]:
    try:
        scene = Scene.from_json(scene_path)
    except Exception:
        scene = Scene.from_dict(
            {
                "scene_id": "invalid_scene",
                "robot": {
                    "robot_id": "unknown_robot",
                    "model_type": "mock_6dof",
                },
                "obstacles": [],
                "safety_config": {},
            }
        )
    try:
        command = JointCommand.from_json(command_path)
    except Exception:
        command = JointCommand(
            command_id="invalid_command",
            command_type="joint_move",
            current_joints=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            target_joints=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            speed=0.1,
            source="invalid_input",
        )
    return scene, command
