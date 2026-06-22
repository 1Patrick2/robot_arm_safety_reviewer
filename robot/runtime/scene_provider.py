from __future__ import annotations

from pathlib import Path
from typing import Protocol

from robot.safety.models import Scene

from .types import RobotObservation


class SceneProvider(Protocol):
    name: str

    def get_scene(self, observation: RobotObservation) -> Scene:
        ...


class StaticSceneProvider:
    name = "static_scene"

    def __init__(self, scene_path: str | Path) -> None:
        self.scene_path = Path(scene_path)
        self.scene = Scene.from_json(self.scene_path)

    def get_scene(self, observation: RobotObservation) -> Scene:
        return self.scene
