from pathlib import Path

from robot_arm.evaluator import evaluate_strategies
from robot_arm.models import RobotArmScene

ROOT = Path(__file__).resolve().parents[1]


def _scene(name: str) -> RobotArmScene:
    return RobotArmScene.from_json(ROOT / f"bench/robot_arm/{name}/scene.json")


def test_simple_reach_accepts_direct_reach():
    results = evaluate_strategies(_scene("simple_3d_reach_001"))

    assert results[0].strategy == "direct_reach"
    assert results[0].accepted


def test_obstacle_scene_prefers_high_clearance_over_direct_reach():
    results = {item.strategy: item for item in evaluate_strategies(_scene("reach_over_obstacle_001"))}

    assert results["high_clearance_reach"].accepted
    assert not results["direct_reach"].collision_free


def test_unreachable_target_accepts_reposition_request():
    results = evaluate_strategies(_scene("unreachable_target_001"))

    assert results[0].strategy == "ask_reposition"
    assert results[0].accepted


def test_joint_limit_scene_accepts_reposition_request():
    results = evaluate_strategies(_scene("joint_limit_risk_001"))

    assert results[0].strategy == "ask_reposition"
    assert results[0].accepted
