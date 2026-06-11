"""Stage 1 joint-space command evaluator.
安全审查主入口，输入是 Scene 和 JointCommand，输出是 SafetyResult。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import JointCommand, SafetyResult, Scene, Violation
from .safety_rules import check_trajectory_joint_limits, classify_risk_level, make_decision
from .trajectory import compute_max_joint_delta, interpolate_joint_trajectory
from sim.mock_backend import MockGeometryBackend


@dataclass(frozen=True)
class EvaluationOutcome:
    safety_result: SafetyResult
    backend_metadata: dict[str, Any]


# 评审函数，核心函数。负责内容为：
# 1. 验证输入的命令和场景是否合法，比如维度是否匹配，必填字段是否存在等。
# 2. 对输入的 joint command 进行插值，生成一个平滑的轨迹，便于后续的碰撞检查和安全评估。
# 3. 检查插值轨迹是否满足关节限制，如果有违规项，记录下来。
# 4. 对插值轨迹进行碰撞检查，获取碰撞结果和相关元数据。
# 5. 根据关节限制检查和碰撞检查的结果，构建违规项列表，并根据安全配置中的阈值进行风险等级分类和决策制定。
def evaluate_joint_command(scene: Scene, command: JointCommand, backend=None) -> SafetyResult:
    """Review a 6-DOF joint-space command before simulated execution."""
    return evaluate_joint_command_with_metadata(scene, command, backend=backend).safety_result


def evaluate_joint_command_with_metadata(scene: Scene, command: JointCommand, backend=None) -> EvaluationOutcome:
    """Review a command and return safety result plus explicit backend metadata."""

    # 1 检查command维度是否和scene.robot.joint_names匹配，即关节数量就对得上
    joint_count = len(scene.robot.joint_names)
    if len(command.current_joints) != joint_count or len(command.target_joints) != joint_count:
        raise ValueError("command joint dimension must match scene robot joint_names")

    # 插值轨迹，把当前到m目标的关节状态插值成一系列中间状态，系统检查不是单点，而是整个轨迹的安全性
    trajectory = interpolate_joint_trajectory(
        command.current_joints,
        command.target_joints,
        scene.safety_config.num_interpolation_steps,
    )

    # 计算最大关节变化量，检查轨迹是否满足关节限制
    max_joint_delta = compute_max_joint_delta(command.current_joints, command.target_joints)

    joint_limits_ok, joint_violations = check_trajectory_joint_limits(trajectory, scene.robot.joint_limits)

    # 选择几何后端进行碰撞检测，默认使用 MockGeometryBackend，可以替换成实际的几何库后端
    review_backend = backend or MockGeometryBackend()
    # 不关系具体后端怎么计算碰撞，但返回统一的结果格式，包括是否碰撞、最小 clearance、最近的 link 和 obstacle、最严重的 step 等信息
    collision_result = review_backend.replay_joint_trajectory(scene=scene, trajectory=trajectory)
    # 保存碰撞检查的元数据到 review_backend 对象中
    backend_metadata = _build_backend_metadata(collision_result)

    # 汇总违规信息列表
    violations: list[Violation] = []
    violations.extend(joint_violations)
    violations.extend(collision_result.violations)

    # 一定是先判断碰撞结果，如果碰撞了，才有 clearance 违规；如果没碰撞，才根据 clearance 阈值判断是否有 clearance 违规。最后再判断 joint delta 违规。这样才能保证违规项的准确性和合理性。
    if collision_result.collision_free:
        if collision_result.min_clearance < scene.safety_config.min_clearance:
            violations.append(
                Violation(
                    type="clearance_violation",
                    message=(
                        f"Minimum clearance {collision_result.min_clearance:.3f} m is below hard "
                        f"threshold {scene.safety_config.min_clearance:.3f} m."
                    ),
                    object=collision_result.closest_obstacle,
                    link=collision_result.closest_robot_link,
                    step=collision_result.worst_step,
                    clearance=collision_result.min_clearance,
                )
            )
        elif collision_result.min_clearance < scene.safety_config.manual_review_clearance:
            violations.append(
                Violation(
                    type="low_clearance",
                    message=(
                        f"Minimum clearance {collision_result.min_clearance:.3f} m is below manual review "
                        f"threshold {scene.safety_config.manual_review_clearance:.3f} m."
                    ),
                    object=collision_result.closest_obstacle,
                    link=collision_result.closest_robot_link,
                    step=collision_result.worst_step,
                    clearance=collision_result.min_clearance,
                )
            )

    # 如果最大关节变化过大，就添加该违规项
    if max_joint_delta > scene.safety_config.max_joint_delta:
        violations.append(
            Violation(
                type="large_joint_delta",
                message=(
                    f"Maximum joint delta {max_joint_delta:.3f} rad exceeds manual review "
                    f"threshold {scene.safety_config.max_joint_delta:.3f} rad."
                ),
                value=round(max_joint_delta, 6),
            )
        )

    # 分类风险等级和制定决策
    risk_level = classify_risk_level(
        joint_limits_ok=joint_limits_ok,
        collision_free=collision_result.collision_free,
        min_clearance=collision_result.min_clearance,
        max_joint_delta=max_joint_delta,
        config=scene.safety_config,
    )
    decision = make_decision(
        joint_limits_ok=joint_limits_ok,
        collision_free=collision_result.collision_free,
        min_clearance=collision_result.min_clearance,
        max_joint_delta=max_joint_delta,
        config=scene.safety_config,
    )

    # 最后构造 SafetyResult 对象，包含所有的评审结果和相关信息，返回给调用者
    safety_result = SafetyResult(
        scene_id=scene.scene_id,
        command_id=command.command_id,
        decision=decision,
        risk_level=risk_level,
        joint_limits_ok=joint_limits_ok,
        trajectory_collision_free=collision_result.collision_free,
        self_collision_checked=False,
        self_collision_free=None,
        min_clearance=round(collision_result.min_clearance, 6),
        closest_robot_link=collision_result.closest_robot_link,
        closest_obstacle=collision_result.closest_obstacle,
        worst_step=collision_result.worst_step,
        max_joint_delta=round(max_joint_delta, 6),
        violations=tuple(violations),
        evidence=tuple(_build_evidence(scene, collision_result, joint_limits_ok, max_joint_delta, decision)),
    )
    return EvaluationOutcome(safety_result=safety_result, backend_metadata=backend_metadata)


def _build_backend_metadata(collision_result) -> dict[str, Any]:
    metadata = {"name": collision_result.backend_name}
    metadata.update(collision_result.metadata)
    return metadata


# 以下是一些辅助函数，用于构建评审结果中的证据列表，包含对关节限制检查、碰撞检查、clearance 数值、joint delta 数值和最终决策的描述性文本来给人可读解释。
def _build_evidence(scene, collision_result, joint_limits_ok: bool, max_joint_delta: float, decision: str) -> list[str]:
    evidence = []
    evidence.append(
        "All joints remain within configured limits."
        if joint_limits_ok
        else "At least one interpolated joint state violates configured limits."
    )
    if collision_result.collision_free:
        evidence.append("Interpolated trajectory is collision-free against sphere obstacles.")
    else:
        evidence.append(
            f"Interpolated trajectory collides with {collision_result.closest_obstacle} "
            f"near {collision_result.closest_robot_link} at step {collision_result.worst_step}."
        )
    evidence.append(
        f"Minimum clearance is {collision_result.min_clearance:.3f} m; required threshold is "
        f"{scene.safety_config.min_clearance:.3f} m and manual-review threshold is "
        f"{scene.safety_config.manual_review_clearance:.3f} m."
    )
    evidence.append(f"Maximum joint delta is {max_joint_delta:.3f} rad.")
    evidence.append(f"Safety gate decision is {decision}.")
    return evidence
