from __future__ import annotations

from robot_safety.evaluator import evaluate_joint_command_with_metadata
from robot_safety.models import JointCommand

from .action_source import ActionSource
from .device import RobotDeviceAdapter
from .episode_recorder import EpisodeRecorder
from .scene_provider import SceneProvider
from .types import RobotAction, RobotObservation, RuntimeStepResult


def action_to_joint_command(observation: RobotObservation, action: RobotAction, *, step_id: str) -> JointCommand:
    return JointCommand(
        command_id=f"runtime_{step_id}",
        command_type=action.action_type,
        current_joints=observation.joint_positions,
        target_joints=action.target_joints,
        speed=action.speed,
        source=action.source,
    )


class SafetyRuntime:
    def __init__(
        self,
        *,
        robot: RobotDeviceAdapter,
        action_source: ActionSource,
        scene_provider: SceneProvider,
        backend,
        recorder: EpisodeRecorder | None = None,
    ) -> None:
        self.robot = robot
        self.action_source = action_source
        self.scene_provider = scene_provider
        self.backend = backend
        self.recorder = recorder
        self._step_index = 0

    def step(self) -> RuntimeStepResult:
        self._step_index += 1
        step_id = f"step_{self._step_index:06d}"
        observation = self.robot.get_observation()
        action = self.action_source.propose_action(observation)
        scene = self.scene_provider.get_scene(observation)
        command = action_to_joint_command(observation, action, step_id=step_id)
        outcome = evaluate_joint_command_with_metadata(scene, command, backend=self.backend)

        sent_action = None
        execution_result = None
        executed = False
        blocked_reason = _blocked_reason(outcome.safety_result.decision)
        if outcome.safety_result.decision == "approve":
            execution_result = self.robot.send_action(action)
            sent_action = action
            executed = execution_result.success
            blocked_reason = None

        result = RuntimeStepResult(
            step_id=step_id,
            observation=observation,
            proposed_action=action,
            safety_result=outcome.safety_result,
            backend_metadata=outcome.backend_metadata,
            executed=executed,
            sent_action=sent_action,
            execution_result=execution_result,
            blocked_reason=blocked_reason,
        )
        if self.recorder is not None:
            result = RuntimeStepResult(
                step_id=result.step_id,
                observation=result.observation,
                proposed_action=result.proposed_action,
                safety_result=result.safety_result,
                backend_metadata=result.backend_metadata,
                executed=result.executed,
                sent_action=result.sent_action,
                execution_result=result.execution_result,
                blocked_reason=result.blocked_reason,
                episode_id=self.recorder.episode_id,
                step_index=self._step_index,
            )
            path = self.recorder.record_step(result)
            result = RuntimeStepResult(
                step_id=result.step_id,
                observation=result.observation,
                proposed_action=result.proposed_action,
                safety_result=result.safety_result,
                backend_metadata=result.backend_metadata,
                executed=result.executed,
                sent_action=result.sent_action,
                execution_result=result.execution_result,
                blocked_reason=result.blocked_reason,
                episode_id=result.episode_id,
                step_index=result.step_index,
                episode_step_path=path,
            )
        return result


def _blocked_reason(decision: str) -> str:
    if decision == "manual_review":
        return "manual_review_required"
    if decision == "reject":
        return "rejected_by_safety_gate"
    return "approved_by_safety_gate"
