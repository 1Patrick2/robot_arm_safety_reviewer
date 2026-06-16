from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from robot_runtime.action_sequence import PolicyActionSequence
from robot_runtime.adapters import create_robot_device
from robot_runtime.episode_recorder import EpisodeRecorder
from robot_runtime.policy_action import policy_action_to_robot_action
from robot_runtime.safety_runtime import SafetyRuntime
from robot_runtime.scene_provider import StaticSceneProvider
from robot_runtime.types import RobotAction, RobotObservation, RuntimeStepResult
from sim.backend_factory import create_backend

from .core import AppResult, ArtifactRef


@dataclass(frozen=True)
class SequenceRuntimeRequest:
    sequence_path: Path
    scene_path: Path
    backend_name: str = "mock"
    device_name: str = "mock_realman"
    episode_root: Path = Path("output_reports/sequence_runtime")
    stop_on_block: bool = True
    run_mode: str = "sequence_runtime"


@dataclass(frozen=True)
class SequenceRuntimeResult:
    sequence_id: str
    backend_name: str
    device_name: str
    episode_dir: Path
    total_steps: int
    approved_steps: int
    executed_steps: int
    blocked_steps: int
    rejected_steps: int
    manual_review_steps: int
    step_results: tuple[RuntimeStepResult, ...]

    def to_dict(self) -> dict:
        return {
            "sequence_id": self.sequence_id,
            "backend": self.backend_name,
            "device": self.device_name,
            "episode_dir": str(self.episode_dir),
            "total_steps": self.total_steps,
            "approved_steps": self.approved_steps,
            "executed_steps": self.executed_steps,
            "blocked_steps": self.blocked_steps,
            "rejected_steps": self.rejected_steps,
            "manual_review_steps": self.manual_review_steps,
            "step_results": [step.to_dict() for step in self.step_results],
        }

    def to_app_result(self) -> AppResult:
        return AppResult(
            ok=True,
            mode="sequence_runtime",
            data=self.to_dict(),
            artifacts=(
                ArtifactRef(
                    kind="runtime_episode",
                    path=self.episode_dir,
                    description="Sequence runtime episode directory",
                ),
            ),
        )


class SequenceActionSource:
    def __init__(self, sequence: PolicyActionSequence) -> None:
        self.sequence = sequence
        self.name = f"policy_sequence:{sequence.sequence_id}"
        self._next_index = 0

    def propose_action(self, observation: RobotObservation) -> RobotAction:
        if self._next_index >= len(self.sequence.actions):
            raise StopIteration("policy action sequence is exhausted")

        sequence_step_index = self._next_index + 1
        policy_action = self.sequence.actions[self._next_index]
        self._next_index += 1

        robot_action = policy_action_to_robot_action(observation, policy_action)
        metadata = dict(robot_action.metadata)
        metadata["sequence_id"] = self.sequence.sequence_id
        metadata["sequence_step_index"] = sequence_step_index
        return RobotAction(
            action_type=robot_action.action_type,
            target_joints=robot_action.target_joints,
            speed=robot_action.speed,
            source=robot_action.source,
            metadata=metadata,
        )


def run_sequence_runtime(request: SequenceRuntimeRequest) -> SequenceRuntimeResult:
    sequence_path = Path(request.sequence_path)
    scene_path = Path(request.scene_path)
    if not sequence_path.exists():
        raise FileNotFoundError(f"sequence file not found: {sequence_path}")
    if not scene_path.exists():
        raise FileNotFoundError(f"scene file not found: {scene_path}")

    sequence = PolicyActionSequence.from_json(sequence_path)
    action_source = SequenceActionSource(sequence)
    scene_provider = StaticSceneProvider(scene_path)
    robot = create_robot_device(request.device_name, initial_joints=sequence.initial_joints)
    backend = create_backend(request.backend_name)
    recorder = EpisodeRecorder(
        root_dir=request.episode_root,
        robot_name=robot.name,
        action_source_name=action_source.name,
        scene_provider_name=scene_provider.name,
        backend_name=request.backend_name,
        run_mode=request.run_mode,
        sequence_id=sequence.sequence_id,
        device_name=request.device_name,
        scene_path=str(request.scene_path),
    )
    runtime = SafetyRuntime(
        robot=robot,
        action_source=action_source,
        scene_provider=scene_provider,
        backend=backend,
        recorder=recorder,
    )

    step_results: list[RuntimeStepResult] = []
    try:
        robot.connect()
        for _ in sequence.actions:
            step_result = runtime.step()
            step_results.append(step_result)
            if step_result.safety_result.decision != "approve" and request.stop_on_block:
                break
    finally:
        robot.disconnect()

    return _build_result(
        sequence_id=sequence.sequence_id,
        backend_name=request.backend_name,
        device_name=request.device_name,
        episode_dir=recorder.episode_dir,
        step_results=tuple(step_results),
    )


def _build_result(
    *,
    sequence_id: str,
    backend_name: str,
    device_name: str,
    episode_dir: Path,
    step_results: tuple[RuntimeStepResult, ...],
) -> SequenceRuntimeResult:
    executed_steps = sum(1 for step in step_results if step.executed)
    approved_steps = sum(1 for step in step_results if step.safety_result.decision == "approve")
    rejected_steps = sum(1 for step in step_results if step.safety_result.decision == "reject")
    manual_review_steps = sum(1 for step in step_results if step.safety_result.decision == "manual_review")
    blocked_steps = sum(1 for step in step_results if not step.executed)
    return SequenceRuntimeResult(
        sequence_id=sequence_id,
        backend_name=backend_name,
        device_name=device_name,
        episode_dir=episode_dir,
        total_steps=len(step_results),
        approved_steps=approved_steps,
        executed_steps=executed_steps,
        blocked_steps=blocked_steps,
        rejected_steps=rejected_steps,
        manual_review_steps=manual_review_steps,
        step_results=step_results,
    )
