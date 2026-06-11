from __future__ import annotations

from typing import Protocol

from .types import RobotAction, RobotObservation


class RobotDeviceAdapter(Protocol):
    name: str

    @property
    def observation_features(self) -> dict:
        ...

    @property
    def action_features(self) -> dict:
        ...

    @property
    def is_connected(self) -> bool:
        ...

    def connect(self, calibrate: bool = True) -> None:
        ...

    def get_observation(self) -> RobotObservation:
        ...

    def send_action(self, action: RobotAction) -> RobotAction:
        ...

    def disconnect(self) -> None:
        ...
