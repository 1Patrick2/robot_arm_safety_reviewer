"""Rule-based safety decisions for joint-space commands."""

from __future__ import annotations

from .models import Decision, JointLimit, RiskLevel, SafetyConfig, Violation


def check_joint_limits(joints: tuple[float, ...] | list[float], joint_limits: tuple[JointLimit, ...]) -> tuple[bool, list[Violation]]:
    """Check one joint state against configured limits."""

    if len(joints) != len(joint_limits):
        raise ValueError("joint dimension does not match joint_limits")

    violations = []
    for index, (value, limit) in enumerate(zip(joints, joint_limits), start=1):
        if value < limit.lower or value > limit.upper:
            violations.append(
                Violation(
                    type="joint_limit",
                    message=f"joint_{index}={value:.3f} is outside [{limit.lower:.3f}, {limit.upper:.3f}].",
                    joint=f"joint_{index}",
                    value=round(float(value), 6),
                    limit=(limit.lower, limit.upper),
                )
            )
    return not violations, violations


def check_trajectory_joint_limits(
    trajectory: list[tuple[float, ...]],
    joint_limits: tuple[JointLimit, ...],
) -> tuple[bool, list[Violation]]:
    """Check all trajectory states against joint limits."""

    all_violations: list[Violation] = []
    for step, joints in enumerate(trajectory):
        _, violations = check_joint_limits(joints, joint_limits)
        for violation in violations:
            all_violations.append(
                Violation(
                    type=violation.type,
                    message=violation.message,
                    joint=violation.joint,
                    step=step,
                    value=violation.value,
                    limit=violation.limit,
                )
            )
    return not all_violations, all_violations


def classify_risk_level(
    *,
    joint_limits_ok: bool,
    collision_free: bool,
    min_clearance: float,
    max_joint_delta: float,
    config: SafetyConfig,
) -> RiskLevel:
    """Map safety signals into low/medium/high risk."""

    if not joint_limits_ok or not collision_free or min_clearance < config.min_clearance:
        return "high"
    if min_clearance < config.manual_review_clearance or max_joint_delta > config.max_joint_delta:
        return "medium"
    return "low"


def make_decision(
    *,
    joint_limits_ok: bool,
    collision_free: bool,
    min_clearance: float,
    max_joint_delta: float,
    config: SafetyConfig,
) -> Decision:
    """Make the safety gate decision."""

    if not joint_limits_ok or not collision_free or min_clearance < config.min_clearance:
        return "reject"
    if min_clearance < config.manual_review_clearance or max_joint_delta > config.max_joint_delta:
        return "manual_review"
    return "approve"

