"""Structured scene models for the 3D robot arm safety reviewer."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEFAULT_STRATEGIES = (
    "direct_reach",
    "elbow_up_reach",
    "elbow_down_reach",
    "high_clearance_reach",
    "ask_reposition",
    "hold_position",
)


@dataclass(frozen=True)
class RobotArm3D:
    links: tuple[float, float, float, float]
    joint_limits: tuple[tuple[float, float], ...]
    current_joints: tuple[float, float, float, float]
    link_radius: float = 0.04


@dataclass(frozen=True)
class Target:
    position: tuple[float, float, float]
    tolerance: float = 0.05


@dataclass(frozen=True)
class SphereObstacle:
    obstacle_id: str
    center: tuple[float, float, float]
    radius: float


@dataclass(frozen=True)
class RobotArmScene:
    scene_id: str
    robot: RobotArm3D
    target: Target
    obstacles: tuple[SphereObstacle, ...]
    candidate_strategies: tuple[str, ...] = DEFAULT_STRATEGIES

    @classmethod
    def from_json(cls, path: str | Path) -> "RobotArmScene":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RobotArmScene":
        scene_id = str(data.get("scene_id", "")).strip()
        if not scene_id:
            raise ValueError("scene_id is required")

        robot_data = data.get("robot")
        if not isinstance(robot_data, dict):
            raise ValueError("robot must be an object")
        robot = RobotArm3D(
            links=_tuple4(robot_data["links"], "robot.links"),
            joint_limits=tuple(
                _limit_pair(item, f"robot.joint_limits[{index}]")
                for index, item in enumerate(robot_data["joint_limits"])
            ),
            current_joints=_tuple4(robot_data.get("current_joints", [0, 0, 0, 0]), "robot.current_joints"),
            link_radius=_positive(robot_data.get("link_radius", 0.04), "robot.link_radius"),
        )
        if len(robot.joint_limits) != 4:
            raise ValueError("robot.joint_limits must contain four limits")

        target_data = data.get("target")
        if not isinstance(target_data, dict):
            raise ValueError("target must be an object")
        target = Target(
            position=_tuple3(target_data["position"], "target.position"),
            tolerance=_positive(target_data.get("tolerance", 0.05), "target.tolerance"),
        )

        obstacles = []
        for raw in data.get("obstacles", []):
            obstacles.append(
                SphereObstacle(
                    obstacle_id=str(raw["id"]),
                    center=_tuple3(raw["center"], f"{raw['id']}.center"),
                    radius=_positive(raw["radius"], f"{raw['id']}.radius"),
                )
            )

        strategies = tuple(data.get("candidate_strategies", DEFAULT_STRATEGIES))
        invalid = sorted(set(strategies).difference(DEFAULT_STRATEGIES))
        if invalid:
            raise ValueError(f"unsupported candidate strategies: {invalid}")

        return cls(
            scene_id=scene_id,
            robot=robot,
            target=target,
            obstacles=tuple(obstacles),
            candidate_strategies=strategies,
        )


@dataclass(frozen=True)
class StrategyEvaluation:
    strategy: str
    ik_feasible: bool
    joint_limits_satisfied: bool
    collision_free: bool
    target_reached: bool
    position_error: float
    selected_joints: tuple[float, float, float, float] | None
    critical_objects: tuple[str, ...]
    score: float
    accepted: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["selected_joints"] = list(self.selected_joints) if self.selected_joints else None
        data["critical_objects"] = list(self.critical_objects)
        return data


def _tuple3(value: Any, field: str) -> tuple[float, float, float]:
    values = tuple(float(item) for item in value)
    if len(values) != 3:
        raise ValueError(f"{field} must contain three numbers")
    return values


def _tuple4(value: Any, field: str) -> tuple[float, float, float, float]:
    values = tuple(float(item) for item in value)
    if len(values) != 4:
        raise ValueError(f"{field} must contain four numbers")
    return values


def _limit_pair(value: Any, field: str) -> tuple[float, float]:
    values = tuple(float(item) for item in value)
    if len(values) != 2 or values[0] > values[1]:
        raise ValueError(f"{field} must be [lower, upper]")
    return values


def _positive(value: Any, field: str) -> float:
    number = float(value)
    if number <= 0:
        raise ValueError(f"{field} must be positive")
    return number
