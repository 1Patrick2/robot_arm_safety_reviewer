from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from robot_runtime.action_source import ReplayActionSource
from robot_runtime.adapters.mock_realman_device import MockRealManDevice
from robot_runtime.episode_recorder import EpisodeRecorder
from robot_runtime.safety_runtime import SafetyRuntime
from robot_runtime.scene_provider import StaticSceneProvider
from robot_runtime.types import RuntimeStepResult
from sim.backend_factory import create_backend


@dataclass(frozen=True)
class RuntimeTaskRequest:
    task_dir: Path
    backend_name: str = "mock"
    episode_root: Path = Path("output_reports/runtime_demo")
    robot_name: str = "mock_realman"


@dataclass(frozen=True)
class RuntimeTaskResult:
    task_dir: Path
    backend_name: str
    episode_dir: Path
    step_result: RuntimeStepResult

    def to_dict(self) -> dict:
        return {
            "task": str(self.task_dir),
            "backend": self.backend_name,
            "episode_dir": str(self.episode_dir),
            "result": self.step_result.to_dict(),
        }


def run_runtime_task(request: RuntimeTaskRequest) -> RuntimeTaskResult:
    task_dir = Path(request.task_dir)
    scene_path = task_dir / "scene.json"
    command_path = task_dir / "command.json"
    if not scene_path.exists():
        raise FileNotFoundError(f"scene.json not found: {scene_path}")
    if not command_path.exists():
        raise FileNotFoundError(f"command.json not found: {command_path}")

    action_source = ReplayActionSource(command_path)
    scene_provider = StaticSceneProvider(scene_path)
    robot = MockRealManDevice(initial_joints=action_source.command.current_joints)
    backend = create_backend(request.backend_name)
    recorder = EpisodeRecorder(
        root_dir=request.episode_root,
        robot_name=robot.name,
        action_source_name=action_source.name,
        scene_provider_name=scene_provider.name,
        backend_name=request.backend_name,
    )
    runtime = SafetyRuntime(
        robot=robot,
        action_source=action_source,
        scene_provider=scene_provider,
        backend=backend,
        recorder=recorder,
    )
    try:
        robot.connect()
        step_result = runtime.step()
    finally:
        robot.disconnect()

    return RuntimeTaskResult(
        task_dir=task_dir,
        backend_name=request.backend_name,
        episode_dir=recorder.episode_dir,
        step_result=step_result,
    )

