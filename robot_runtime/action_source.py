from __future__ import annotations

from pathlib import Path
from typing import Protocol

from robot_safety.models import JointCommand

from .types import RobotAction, RobotObservation


class ActionSource(Protocol):
    name: str

    def propose_action(self, observation: RobotObservation) -> RobotAction:
        ...


class ReplayActionSource:
    name = "replay"

    def __init__(self, command_path: str | Path) -> None:
        self.command_path = Path(command_path)
        self.command = JointCommand.from_json(self.command_path)

    def propose_action(self, observation: RobotObservation) -> RobotAction:
        return RobotAction(
            action_type=self.command.command_type,
            target_joints=self.command.target_joints,
            speed=self.command.speed,
            source="replay",
            metadata={
                "command_id": self.command.command_id,
                "command_path": str(self.command_path),
                "original_source": self.command.source,
            },
        )
