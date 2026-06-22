"""Common simulation backend interfaces.
定义了所有后端返回的结果格式，以及后端需要实现的接口协议。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from robot.safety.models import Violation

# 统一后端返回结果格式，包含碰撞检查结果和一些元信息
'''最重要的事metadata字段，可以包含后端特有的额外信息，比如碰撞检查的详细数据、性能指标等。包括mock和pybullet后端都要返回这个格式，方便统一处理和比较。'''
@dataclass(frozen=True)
class BackendReviewResult:
    backend_name: str
    collision_free: bool
    min_clearance: float
    closest_robot_link: str | None
    closest_obstacle: str | None
    worst_step: int | None
    violations: tuple[Violation, ...]
    metadata: dict[str, Any]

'''定义了一个protocol，只要有一个类有name属性和replay_joint_trajectory方法，就可以被认为是SimulationBackend类型去使用。这就是结构化接口的好处，不需要显式继承某个基类，只要符合接口要求就行。'''
class SimulationBackend(Protocol):
    name: str

    def replay_joint_trajectory(self, *, scene, trajectory: list[tuple[float, ...]]) -> BackendReviewResult:
        """Replay a joint trajectory and return collision/clearance evidence."""
