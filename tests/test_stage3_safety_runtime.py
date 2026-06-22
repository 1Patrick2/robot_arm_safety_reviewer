from pathlib import Path

from robot.runtime.action_source import ReplayActionSource
from robot.runtime.adapters.mock_realman_device import MockRealManDevice
from robot.runtime.episode_recorder import EpisodeRecorder
from robot.runtime.safety_runtime import SafetyRuntime, action_to_joint_command
from robot.runtime.scene_provider import StaticSceneProvider
from robot.runtime.types import RobotAction, RobotObservation
from robot.backends.backend_factory import create_backend


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_action_to_joint_command_uses_observation_and_action():
    observation = RobotObservation("mock_realman_6dof", (0.0,) * 6, "2026-06-11T10:00:00Z")
    action = RobotAction("joint_move", (0.1,) * 6, speed=0.2, source="replay")

    command = action_to_joint_command(observation, action, step_id="step_000001")

    assert command.command_id == "runtime_step_000001"
    assert command.current_joints == (0.0,) * 6
    assert command.target_joints == (0.1,) * 6
    assert command.speed == 0.2
    assert command.source == "replay"


def _runtime_for_task(task_name: str, tmp_path):
    task_dir = BENCH / task_name
    robot = MockRealManDevice(initial_joints=(0.0,) * 6)
    robot.connect()
    action_source = ReplayActionSource(task_dir / "command.json")
    scene_provider = StaticSceneProvider(task_dir / "scene.json")
    recorder = EpisodeRecorder(
        root_dir=tmp_path,
        robot_name=robot.name,
        action_source_name=action_source.name,
        scene_provider_name=scene_provider.name,
        backend_name="mock",
    )
    return SafetyRuntime(
        robot=robot,
        action_source=action_source,
        scene_provider=scene_provider,
        backend=create_backend("mock"),
        recorder=recorder,
    ), robot


def test_safety_runtime_executes_approved_action(tmp_path):
    runtime, robot = _runtime_for_task("simple_joint_move_001", tmp_path)

    result = runtime.step()

    assert result.safety_result.decision == "approve"
    assert result.executed is True
    assert result.sent_action is not None
    assert result.execution_result is not None
    assert result.execution_result.attempted is True
    assert result.execution_result.success is True
    assert result.execution_result.reason == "executed"
    assert result.execution_result.metadata["execution_count"] == 1
    assert robot.execution_count == 1


def test_safety_runtime_blocks_rejected_action(tmp_path):
    runtime, robot = _runtime_for_task("obstacle_collision_001", tmp_path)

    result = runtime.step()

    assert result.safety_result.decision == "reject"
    assert result.executed is False
    assert result.sent_action is None
    assert result.execution_result is None
    assert result.blocked_reason == "rejected_by_safety_gate"
    assert robot.execution_count == 0


def test_safety_runtime_blocks_manual_review_action(tmp_path):
    runtime, robot = _runtime_for_task("near_miss_clearance_001", tmp_path)

    result = runtime.step()

    assert result.safety_result.decision == "manual_review"
    assert result.executed is False
    assert result.sent_action is None
    assert result.execution_result is None
    assert result.blocked_reason == "manual_review_required"
    assert robot.execution_count == 0
