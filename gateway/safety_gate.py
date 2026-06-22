'''Pre-execution safety gate for joint-space robot commands.
安全网关主入口，定义了两个对外函数review_only与execute_if_safe，分别对应仅审查和审查后执行两种模式。'''

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from robot_safety.evaluator import evaluate_joint_command_with_metadata
from robot_safety.models import JointCommand, SafetyResult, Scene, Violation
from robots.base import RobotAdapter
from robots.mock_realman_6dof import MockRealMan6DoFAdapter
from robot.backends.backend_factory import create_backend

from .execution_logger import build_execution_log, write_execution_log


'''返回值包含三件事，本次安全审查结论，完整日志以及日志文件路径'''
@dataclass(frozen=True)
class ReviewOutcome:
    safety_result: SafetyResult
    execution_log: dict
    log_path: Path | None

'''只审查，不执行'''
def review_only(
    scene_path: str | Path,
    command_path: str | Path,
    *,
    backend_name: str = "mock",
    log_dir: str | Path | None = "logs",
) -> ReviewOutcome:
    """Review a command and write a replayable log without simulated execution."""
    '''如果中间出错，就会进入except分支，尽可能从输入文件中提取场景和命令信息，构造一个无效命令的结果，并记录日志。'''
    try:
        scene = Scene.from_json(scene_path)
        command = JointCommand.from_json(command_path)
        backend = create_backend(backend_name)
        outcome = evaluate_joint_command_with_metadata(scene, command, backend=backend)
        result = outcome.safety_result
        review_backend = outcome.backend_metadata
    except Exception as exc:
        scene, command = _best_effort_context(scene_path, command_path)
        '''构造一个无效命令的结果，包含错误信息，并标记为高风险，拒绝执行。失败是不会直接崩溃的，而是会有一个合理的失败结果返回。'''
        result = _invalid_command_result(scene.scene_id, command.command_id, str(exc))
        review_backend = {"name": backend_name}
    payload = build_execution_log(
        scene=scene,
        command=command,
        safety_result=result,
        executed=False,
        reason="review_only",
        mode="review_only",
        scene_path=scene_path,
        command_path=command_path,
        review_backend=review_backend,
    )
    log_path = write_execution_log(payload, log_dir) if log_dir is not None else None
    return ReviewOutcome(safety_result=result, execution_log=payload, log_path=log_path)

'''审查通过才执行，执行结果也会记录在日志里'''
def execute_if_safe(
    scene_path: str | Path,
    command_path: str | Path,
    *,
    robot_adapter: RobotAdapter | None = None,
    backend_name: str = "mock",
    log_dir: str | Path | None = "logs",
) -> ReviewOutcome:
    """Review a command and simulate execution only when the safety gate approves it."""

    try:
        scene = Scene.from_json(scene_path)
        command = JointCommand.from_json(command_path)
        backend = create_backend(backend_name)
        outcome = evaluate_joint_command_with_metadata(scene, command, backend=backend)
        result = outcome.safety_result
        review_backend = outcome.backend_metadata
    except Exception as exc:
        scene, command = _best_effort_context(scene_path, command_path)
        result = _invalid_command_result(scene.scene_id, command.command_id, str(exc))
        review_backend = {"name": backend_name}
    adapter_result = None
    executed = False
    reason = _execution_reason(result.decision)
    '''这里是和review_only的区别，只有approve才会进入RobotAdapter，其他情况都不会执行，直接记录日志。'''
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
        review_backend=review_backend,
    )
    log_path = write_execution_log(payload, log_dir) if log_dir is not None else None
    return ReviewOutcome(safety_result=result, execution_log=payload, log_path=log_path)


def _execution_reason(decision: str) -> str:
    if decision == "approve":
        return "approved_by_safety_gate"
    if decision == "manual_review":
        return "manual_review_required"
    return "rejected_by_safety_gate"

'''生成后端元数据，包含后端名称和可能的额外信息，供日志记录和后续分析使用。'''

'''异常输入统一变reject处理，构造包含错误信息的结果'''
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

'''异常情况也需要保留上下文，能读scene和command的信息，就保留，否则构造invalid值'''
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
