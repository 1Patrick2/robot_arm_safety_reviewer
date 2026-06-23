"""Replayable execution log writer for safety reviews."""

from __future__ import annotations

import json
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from robot.safety.models import JointCommand, SafetyResult, Scene

'''完整记录原始scene,command，安全审查结果，后端信息，执行信息和环境信息等，生成一个结构化的日志，方便后续分析和回放。'''
def build_execution_log(
    *,
    scene: Scene,
    command: JointCommand,
    safety_result: SafetyResult,
    executed: bool,
    reason: str,
    mode: str,
    scene_path: str | Path | None = None,
    command_path: str | Path | None = None,
    adapter_result: dict[str, Any] | None = None,
    review_backend: dict[str, Any] | None = None,
    log_id: str | None = None,
) -> dict[str, Any]:
    """Build a replayable safety review log payload."""

    now = datetime.now(timezone.utc)
    resolved_log_id = log_id or f"exec_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    return {
        "schema_version": "stage1.execution_log.v1",
        "log_id": resolved_log_id,
        "timestamp": now.isoformat(),
        "mode": mode,
        "scene_id": scene.scene_id,
        "command_id": command.command_id,
        "robot": scene.robot.robot_id,
        "input_paths": {
            "scene_path": str(scene_path) if scene_path is not None else None,
            "command_path": str(command_path) if command_path is not None else None,
        },
        "review_summary": _review_summary(safety_result),
        "trajectory_summary": _trajectory_summary(scene, safety_result),
        "environment": {
            "backend": (review_backend or {"name": "mock"}).get("name", "mock"),
            "python_version": platform.python_version(),
        },
        "review_backend": review_backend or {"name": "mock"},
        "scene": _scene_payload(scene),
        "command": _command_payload(command),
        "safety_result": safety_result.to_dict(),
        "execution": {
            "executed": executed,
            "reason": reason,
            "adapter_result": adapter_result,
        },
    }

'''提取摘要信息，包含审查决策、风险等级、最小间隙、最近障碍物和机器人链接等，供日志的review_summary字段使用。'''
def _review_summary(result: SafetyResult) -> dict[str, Any]:
    return {
        "decision": result.decision,
        "risk_level": result.risk_level,
        "min_clearance": result.min_clearance,
        "closest_obstacle": result.closest_obstacle,
        "closest_robot_link": result.closest_robot_link,
        "worst_step": result.worst_step,
    }

'''提取轨迹相关的摘要信息，包含轨迹是否碰撞、最小间隙、最严重的步骤等，供日志的trajectory_summary字段使用。'''
def _trajectory_summary(scene: Scene, result: SafetyResult) -> dict[str, Any]:
    return {
        "num_steps": scene.safety_config.num_interpolation_steps,
        "worst_step": result.worst_step,
        "max_joint_delta": result.max_joint_delta,
        "min_clearance": result.min_clearance,
        "collision_free": result.trajectory_collision_free,
    }

# 写日志的函数，生成一个JSON文件，文件名包含时间戳和随机ID，内容是结构化的执行日志，方便后续分析和回放。
def write_execution_log(payload: dict[str, Any], log_dir: str | Path = "logs") -> Path:
    """Write a JSON execution log and return the created path."""

    output_dir = Path(log_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_id = str(payload.get("log_id", "exec_unknown"))
    path = output_dir / f"{log_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

'''安全审查的结果和执行结果都记录在日志里，形成一个完整的审查和执行记录，方便后续分析和回放。'''
def _scene_payload(scene: Scene) -> dict[str, Any]:
    return {
        "scene_id": scene.scene_id,
        "robot": {
            "robot_id": scene.robot.robot_id,
            "model_type": scene.robot.model_type,
            "model_version": scene.robot.model_version,
            "joint_names": list(scene.robot.joint_names),
            "link_lengths": list(scene.robot.link_lengths),
            "link_radius": scene.robot.link_radius,
            "base_position": list(scene.robot.base_position),
            "base_orientation": list(scene.robot.base_orientation),
            "joint_limits": [
                {"lower": limit.lower, "upper": limit.upper}
                for limit in scene.robot.joint_limits
            ],
        },
        "obstacles": [
            {
                "type": "sphere",
                "obstacle_id": item.obstacle_id,
                "position": list(item.position),
                "radius": item.radius,
            }
            for item in scene.obstacles
        ],
        "safety_config": {
            "min_clearance": scene.safety_config.min_clearance,
            "manual_review_clearance": scene.safety_config.manual_review_clearance,
            "max_joint_delta": scene.safety_config.max_joint_delta,
            "num_interpolation_steps": scene.safety_config.num_interpolation_steps,
            "check_self_collision": scene.safety_config.check_self_collision,
        },
    }


def _command_payload(command: JointCommand) -> dict[str, Any]:
    return {
        "command_id": command.command_id,
        "command_type": command.command_type,
        "current_joints": list(command.current_joints),
        "target_joints": list(command.target_joints),
        "speed": command.speed,
        "source": command.source,
    }
