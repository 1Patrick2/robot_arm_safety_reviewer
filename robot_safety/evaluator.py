"""Stage 1 joint-space command evaluator."""

from __future__ import annotations

from .collision import check_trajectory_collision
from .models import JointCommand, SafetyResult, Scene, Violation
from .safety_rules import check_trajectory_joint_limits, classify_risk_level, make_decision
from .trajectory import compute_max_joint_delta, interpolate_joint_trajectory


def evaluate_joint_command(scene: Scene, command: JointCommand) -> SafetyResult:
    """Review a 6-DOF joint-space command before simulated execution."""

    joint_count = len(scene.robot.joint_names)
    if len(command.current_joints) != joint_count or len(command.target_joints) != joint_count:
        raise ValueError("command joint dimension must match scene robot joint_names")

    trajectory = interpolate_joint_trajectory(
        command.current_joints,
        command.target_joints,
        scene.safety_config.num_interpolation_steps,
    )
    max_joint_delta = compute_max_joint_delta(command.current_joints, command.target_joints)
    joint_limits_ok, joint_violations = check_trajectory_joint_limits(trajectory, scene.robot.joint_limits)
    collision_result = check_trajectory_collision(trajectory, scene.robot, scene.obstacles)

    violations: list[Violation] = []
    violations.extend(joint_violations)
    violations.extend(collision_result.violations)
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

    return SafetyResult(
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
