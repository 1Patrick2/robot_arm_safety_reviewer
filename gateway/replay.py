"""Replay execution logs and verify deterministic safety-review consistency."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robot.safety.evaluator import evaluate_joint_command
from robot.safety.models import JointCommand, Scene

from .safety_gate import review_only


def replay_log(log_path: str | Path) -> dict[str, Any]:
    """Recompute a safety result from a replayable log and compare key fields."""

    path = Path(log_path)
    original = json.loads(path.read_text(encoding="utf-8"))
    recomputed_result = _recompute_result(original)
    recomputed = recomputed_result.to_dict()
    checks = {
        "decision_match": recomputed.get("decision") == original["safety_result"].get("decision"),
        "risk_match": recomputed.get("risk_level") == original["safety_result"].get("risk_level"),
        "min_clearance_match": _close(
            recomputed.get("min_clearance"),
            original["safety_result"].get("min_clearance"),
        ),
        "closest_obstacle_match": recomputed.get("closest_obstacle")
        == original["safety_result"].get("closest_obstacle"),
        "violations_match": _violation_types(recomputed) == _violation_types(original["safety_result"]),
    }
    return {
        "log_id": original.get("log_id"),
        "consistent": all(checks.values()),
        "checks": checks,
        "original": _summary(original["safety_result"]),
        "recomputed": _summary(recomputed),
    }


def _recompute_result(payload: dict[str, Any]):
    input_paths = payload.get("input_paths", {})
    scene_path = input_paths.get("scene_path")
    command_path = input_paths.get("command_path")
    if scene_path and command_path and Path(scene_path).exists() and Path(command_path).exists():
        return review_only(scene_path, command_path, log_dir=None).safety_result

    scene = Scene.from_dict(payload["scene"])
    command = JointCommand.from_dict(payload["command"])
    return evaluate_joint_command(scene, command)


def _summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result.get("decision"),
        "risk_level": result.get("risk_level"),
        "min_clearance": result.get("min_clearance"),
        "closest_obstacle": result.get("closest_obstacle"),
        "violations": _violation_types(result),
    }


def _violation_types(result: dict[str, Any]) -> list[str]:
    return [str(item.get("type")) for item in result.get("violations", []) if item.get("type")]


def _close(left: Any, right: Any, *, tolerance: float = 1e-6) -> bool:
    if left is None or right is None:
        return left == right
    return abs(float(left) - float(right)) <= tolerance
