"""Structured models for Stage 1 robot arm safety review."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

Point3D = tuple[float, float, float]
Decision = Literal["approve", "manual_review", "reject"]
RiskLevel = Literal["low", "medium", "high"]

DEFAULT_JOINT_NAMES = ("joint1", "joint2", "joint3", "joint4", "joint5", "joint6")
DEFAULT_LINK_LENGTHS = (0.18, 0.32, 0.28, 0.2, 0.14, 0.1)
DEFAULT_MODEL_VERSION = "mock_realman_6dof_stage1_v1"
DEFAULT_JOINT_LIMITS = (
    (-3.14, 3.14),
    (-1.57, 1.57),
    (-2.2, 2.2),
    (-3.14, 3.14),
    (-1.8, 1.8),
    (-3.14, 3.14),
)


@dataclass(frozen=True)
class JointLimit:
    lower: float
    upper: float


@dataclass(frozen=True)
class RobotModel:
    robot_id: str
    model_type: str
    model_version: str

    '''关节名、关节限制、连杆长度、连杆半径和 base 位姿等参数'''
    joint_names: tuple[str, ...]
    joint_limits: tuple[JointLimit, ...]
    link_lengths: tuple[float, ...]
    link_radius: float
    base_position: Point3D = (0.0, 0.0, 0.0)
    base_orientation: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)


@dataclass(frozen=True)
class JointCommand:
    command_id: str
    command_type: str
    current_joints: tuple[float, ...]
    target_joints: tuple[float, ...]
    speed: float
    source: str = "mock_user"

    @classmethod
    def from_json(cls, path: str | Path) -> "JointCommand":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JointCommand":
        command_type = str(data.get("command_type", "joint_move"))
        if command_type != "joint_move":
            raise ValueError(f"unsupported command_type: {command_type}")
        return cls(
            command_id=_required_str(data, "command_id"),
            command_type=command_type,
            current_joints=_float_tuple(data.get("current_joints"), "current_joints"),
            target_joints=_float_tuple(data.get("target_joints"), "target_joints"),
            speed=_positive(data.get("speed", 0.2), "speed"),
            source=str(data.get("source", "mock_user")),
        )

# 圆形障碍物定义
@dataclass(frozen=True)
class SphereObstacle:
    obstacle_id: str
    position: Point3D
    radius: float

# 定义审查规则的阈值
@dataclass(frozen=True)
class SafetyConfig:
    min_clearance: float = 0.05
    manual_review_clearance: float = 0.10
    max_joint_delta: float = 1.2
    num_interpolation_steps: int = 40
    check_self_collision: bool = False

# 场景定义，包括机器人模型、目标位置和障碍物列表等信息
@dataclass(frozen=True)
class Scene:
    scene_id: str
    robot: RobotModel
    obstacles: tuple[SphereObstacle, ...]
    safety_config: SafetyConfig

    # 读json文件并创建Scene对象
    @classmethod
    def from_json(cls, path: str | Path) -> "Scene":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    # 转成强类型的Scene对象，并进行必要的验证
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scene":
        return cls(
            scene_id=_required_str(data, "scene_id"),
            robot=_robot_from_dict(_required_object(data, "robot")),
            obstacles=tuple(_obstacle_from_dict(item) for item in data.get("obstacles", [])),
            safety_config=_safety_config_from_dict(data.get("safety_config", {})),
        )

# 安全违规项定义，包括违规类型、描述信息、相关对象和数值等，这是证据项
@dataclass(frozen=True)
class Violation:
    type: str
    message: str
    object: str | None = None
    link: str | None = None
    joint: str | None = None
    step: int | None = None
    clearance: float | None = None
    value: float | None = None
    limit: tuple[float, float] | None = None

    # to_dict()会去掉none字段
    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


# 最终审查结果定义，包括决策、风险等级、违规项列表和证据列表等信息
'''SafetyResult 是系统的核心输出。它既包含最终决策 approve/manual_review/reject，也包含风险等级、joint limit 是否通过、轨迹是否碰撞、最小 clearance、最近 link/obstacle、worst step、violations 和 evidence. 其中 violations 是一个 Violation 对象的列表，每个 Violation 包含违规类型、描述信息、相关对象和数值等信息。evidence 是一个字符串列表，包含用于支持决策的证据项，可以是文本描述、数值数据或者其他相关信息。'''
@dataclass(frozen=True)
class SafetyResult:
    scene_id: str
    command_id: str
    decision: Decision
    risk_level: RiskLevel
    joint_limits_ok: bool
    trajectory_collision_free: bool
    self_collision_checked: bool
    self_collision_free: bool | None
    min_clearance: float
    closest_robot_link: str | None
    closest_obstacle: str | None
    worst_step: int | None
    max_joint_delta: float
    violations: tuple[Violation, ...]
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["violations"] = [item.to_dict() for item in self.violations]
        data["evidence"] = list(self.evidence)
        return data

# 以下是一些辅助函数，用于从字典创建强类型对象，并进行必要的验证和错误处理
def _robot_from_dict(data: dict[str, Any]) -> RobotModel:
    joint_names = tuple(str(item) for item in data.get("joint_names", DEFAULT_JOINT_NAMES))
    link_lengths = _positive_float_tuple(data.get("link_lengths", DEFAULT_LINK_LENGTHS), "robot.link_lengths")
    if len(joint_names) != 6:
        raise ValueError("robot.joint_names must contain six names")
    if len(link_lengths) != 6:
        raise ValueError("robot.link_lengths must contain six lengths")

    raw_limits = data.get("joint_limits", DEFAULT_JOINT_LIMITS)
    joint_limits = tuple(_joint_limit(item, f"robot.joint_limits[{index}]") for index, item in enumerate(raw_limits))
    if len(joint_limits) != 6:
        raise ValueError("robot.joint_limits must contain six limits")

    return RobotModel(
        robot_id=_required_str(data, "robot_id"),
        model_type=str(data.get("model_type", "mock_6dof")),
        model_version=str(data.get("model_version", DEFAULT_MODEL_VERSION)),
        base_position=_point3(data.get("base_position", (0.0, 0.0, 0.0)), "robot.base_position"),
        base_orientation=_quat(data.get("base_orientation", (0.0, 0.0, 0.0, 1.0)), "robot.base_orientation"),
        joint_names=joint_names,
        joint_limits=joint_limits,
        link_lengths=link_lengths,
        link_radius=_positive(data.get("link_radius", 0.025), "robot.link_radius"),
    )


def _obstacle_from_dict(data: dict[str, Any]) -> SphereObstacle:
    obstacle_type = str(data.get("type", "sphere"))
    if obstacle_type != "sphere":
        raise ValueError(f"unsupported obstacle type: {obstacle_type}")
    return SphereObstacle(
        obstacle_id=_required_str(data, "obstacle_id"),
        position=_point3(data.get("position"), "obstacle.position"),
        radius=_positive(data.get("radius"), "obstacle.radius"),
    )


def _safety_config_from_dict(data: dict[str, Any]) -> SafetyConfig:
    min_clearance = _positive(data.get("min_clearance", 0.05), "safety_config.min_clearance")
    manual_review_clearance = _positive(
        data.get("manual_review_clearance", 0.10), "safety_config.manual_review_clearance"
    )
    if manual_review_clearance < min_clearance:
        raise ValueError("safety_config.manual_review_clearance must be >= safety_config.min_clearance")
    return SafetyConfig(
        min_clearance=min_clearance,
        manual_review_clearance=manual_review_clearance,
        max_joint_delta=_positive(data.get("max_joint_delta", 1.2), "safety_config.max_joint_delta"),
        num_interpolation_steps=_int_at_least(
            data.get("num_interpolation_steps", 40), "safety_config.num_interpolation_steps", minimum=2
        ),
        check_self_collision=bool(data.get("check_self_collision", False)),
    )


def _required_object(data: dict[str, Any], field: str) -> dict[str, Any]:
    value = data.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _required_str(data: dict[str, Any], field: str) -> str:
    value = str(data.get(field, "")).strip()
    if not value:
        raise ValueError(f"{field} is required")
    return value


def _joint_limit(value: Any, field: str) -> JointLimit:
    if isinstance(value, dict):
        lower = float(value["lower"])
        upper = float(value["upper"])
        if lower > upper:
            raise ValueError(f"{field} lower must be <= upper")
        return JointLimit(lower=lower, upper=upper)
    lower, upper = _float_pair(value, field)
    if lower > upper:
        raise ValueError(f"{field} lower must be <= upper")
    return JointLimit(lower=lower, upper=upper)


def _float_pair(value: Any, field: str) -> tuple[float, float]:
    values = _float_tuple(value, field)
    if len(values) != 2:
        raise ValueError(f"{field} must contain two numbers")
    return values[0], values[1]


def _point3(value: Any, field: str) -> Point3D:
    values = _float_tuple(value, field)
    if len(values) != 3:
        raise ValueError(f"{field} must contain three numbers")
    return values[0], values[1], values[2]


def _quat(value: Any, field: str) -> tuple[float, float, float, float]:
    values = _float_tuple(value, field)
    if len(values) != 4:
        raise ValueError(f"{field} must contain four numbers")
    return values[0], values[1], values[2], values[3]


def _float_tuple(value: Any, field: str) -> tuple[float, ...]:
    try:
        values = tuple(float(item) for item in value)
    except TypeError as exc:
        raise ValueError(f"{field} must be a list of numbers") from exc
    return values


def _positive_float_tuple(value: Any, field: str) -> tuple[float, ...]:
    values = _float_tuple(value, field)
    if any(item <= 0 for item in values):
        raise ValueError(f"{field} values must be positive")
    return values


def _positive(value: Any, field: str) -> float:
    number = float(value)
    if number <= 0:
        raise ValueError(f"{field} must be positive")
    return number


def _int_at_least(value: Any, field: str, *, minimum: int) -> int:
    number = int(value)
    if number < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    return number
