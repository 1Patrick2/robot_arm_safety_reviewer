"""Strategy evaluation CLI for the 3D robot arm safety reviewer."""

from __future__ import annotations

import argparse
import json
import math
from typing import Any

from robot_arm.collision import check_arm_collision, minimum_obstacle_clearance
from robot_arm.kinematics import check_joint_limits, sample_ik_candidates
from robot_arm.models import RobotArmScene, StrategyEvaluation


def evaluate_strategy(scene: RobotArmScene, strategy: str) -> StrategyEvaluation:
    if strategy in {"ask_reposition", "hold_position"}:
        return _evaluate_non_motion_strategy(scene, strategy)

    candidate = _select_candidate(scene, strategy)
    if candidate is None:
        return _failed_motion(strategy, "No IK candidate reaches the target tolerance.")

    joints, position_error, points = candidate
    joint_limits_satisfied = check_joint_limits(joints, scene.robot.joint_limits)
    has_collision, critical_objects = check_arm_collision(
        points,
        scene.obstacles,
        link_radius=scene.robot.link_radius,
    )
    target_reached = position_error <= scene.target.tolerance
    collision_free = not has_collision
    accepted = joint_limits_satisfied and collision_free and target_reached
    score = _motion_score(
        position_error=position_error,
        accepted=accepted,
        collision_free=collision_free,
        joint_limits_satisfied=joint_limits_satisfied,
        clearance=minimum_obstacle_clearance(points, scene.obstacles, link_radius=scene.robot.link_radius),
    ) + _strategy_bias(strategy, has_obstacles=bool(scene.obstacles))
    reason = _motion_reason(strategy, accepted, target_reached, joint_limits_satisfied, collision_free, critical_objects)
    return StrategyEvaluation(
        strategy=strategy,
        ik_feasible=True,
        joint_limits_satisfied=joint_limits_satisfied,
        collision_free=collision_free,
        target_reached=target_reached,
        position_error=round(position_error, 4),
        selected_joints=tuple(round(item, 4) for item in joints),
        critical_objects=critical_objects,
        score=round(score, 4),
        accepted=accepted,
        reason=reason,
    )


def evaluate_strategies(scene: RobotArmScene) -> list[StrategyEvaluation]:
    motion_results = [
        evaluate_strategy(scene, strategy)
        for strategy in scene.candidate_strategies
        if strategy not in {"ask_reposition", "hold_position"}
    ]
    fallback_results = [
        _evaluate_non_motion_strategy(scene, strategy, motion_results)
        for strategy in scene.candidate_strategies
        if strategy in {"ask_reposition", "hold_position"}
    ]
    results = motion_results + fallback_results
    return sorted(
        results,
        key=lambda item: (
            not item.accepted,
            item.score,
            item.strategy,
        ),
    )


def _select_candidate(scene: RobotArmScene, strategy: str):
    candidates = sample_ik_candidates(scene.robot, scene.target)
    reachable = [item for item in candidates if item[1] <= scene.target.tolerance]
    if not reachable:
        return None
    if strategy == "direct_reach":
        return min(reachable, key=lambda item: _joint_motion(item[0], scene.robot.current_joints))
    if strategy == "elbow_up_reach":
        return max(reachable, key=lambda item: item[2][2][2])
    if strategy == "elbow_down_reach":
        return min(reachable, key=lambda item: item[2][2][2])
    if strategy == "high_clearance_reach":
        return max(
            reachable,
            key=lambda item: minimum_obstacle_clearance(
                item[2],
                scene.obstacles,
                link_radius=scene.robot.link_radius,
            ),
        )
    raise ValueError(f"unsupported strategy: {strategy}")


def _evaluate_non_motion_strategy(
    scene: RobotArmScene,
    strategy: str,
    motion_results: list[StrategyEvaluation] | None = None,
) -> StrategyEvaluation:
    motion_results = motion_results if motion_results is not None else [
        evaluate_strategy(scene, item)
        for item in scene.candidate_strategies
        if item not in {"ask_reposition", "hold_position"}
    ]
    has_accepted_motion = any(item.accepted for item in motion_results)
    accepted = not has_accepted_motion
    reason = (
        "No motion strategy is safely accepted; request repositioning."
        if strategy == "ask_reposition"
        else "Hold current position because no safe motion strategy is available."
    )
    return StrategyEvaluation(
        strategy=strategy,
        ik_feasible=False,
        joint_limits_satisfied=True,
        collision_free=True,
        target_reached=False,
        position_error=999.0,
        selected_joints=None,
        critical_objects=tuple(sorted({obj for result in motion_results for obj in result.critical_objects})),
        score=20.0 if accepted and strategy == "ask_reposition" else 25.0 if accepted else 200.0,
        accepted=accepted,
        reason=reason if accepted else "A safe motion strategy exists; fallback is unnecessary.",
    )


def _failed_motion(strategy: str, reason: str) -> StrategyEvaluation:
    return StrategyEvaluation(
        strategy=strategy,
        ik_feasible=False,
        joint_limits_satisfied=False,
        collision_free=False,
        target_reached=False,
        position_error=999.0,
        selected_joints=None,
        critical_objects=(),
        score=500.0,
        accepted=False,
        reason=reason,
    )


def _motion_score(
    *,
    position_error: float,
    accepted: bool,
    collision_free: bool,
    joint_limits_satisfied: bool,
    clearance: float,
) -> float:
    score = position_error * 100.0
    if not joint_limits_satisfied:
        score += 100.0
    if not collision_free:
        score += 1000.0
    if not accepted:
        score += 50.0
    score -= max(min(clearance, 1.0), -1.0)
    return score


def _strategy_bias(strategy: str, *, has_obstacles: bool) -> float:
    if strategy == "direct_reach" and not has_obstacles:
        return -2.0
    return 0.0


def _motion_reason(
    strategy: str,
    accepted: bool,
    target_reached: bool,
    joint_limits_satisfied: bool,
    collision_free: bool,
    critical_objects: tuple[str, ...],
) -> str:
    if accepted:
        return f"{strategy} reaches the target, satisfies joint limits, and is collision-free."
    if not target_reached:
        return f"{strategy} does not reach the target within tolerance."
    if not joint_limits_satisfied:
        return f"{strategy} violates joint limits."
    if not collision_free:
        return f"{strategy} collides with {', '.join(critical_objects)}."
    return f"{strategy} is not accepted."


def _joint_motion(first, second) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate 3D robot arm strategies.")
    parser.add_argument("scene_file")
    args = parser.parse_args()
    scene = RobotArmScene.from_json(args.scene_file)
    payload: dict[str, Any] = {
        "scene_id": scene.scene_id,
        "evaluations": [item.to_dict() for item in evaluate_strategies(scene)],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
