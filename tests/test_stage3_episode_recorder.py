import json

from robot.runtime.episode_recorder import EpisodeRecorder
from robot.runtime.types import RobotAction, RobotObservation, RuntimeExecutionResult, RuntimeStepResult
from robot.safety.models import SafetyResult


def _safe_result():
    return SafetyResult(
        scene_id="scene",
        command_id="cmd",
        decision="approve",
        risk_level="low",
        joint_limits_ok=True,
        trajectory_collision_free=True,
        self_collision_checked=False,
        self_collision_free=None,
        min_clearance=0.2,
        closest_robot_link="link_1",
        closest_obstacle="sphere",
        worst_step=0,
        max_joint_delta=0.1,
        violations=(),
        evidence=("safe",),
    )


def test_episode_recorder_writes_metadata_and_steps_jsonl(tmp_path):
    recorder = EpisodeRecorder(
        root_dir=tmp_path,
        robot_name="mock_realman_device",
        action_source_name="replay",
        scene_provider_name="static_scene",
        backend_name="mock",
    )
    result = RuntimeStepResult(
        step_id="step_000001",
        observation=RobotObservation("mock_realman_6dof", (0.0,) * 6, "2026-06-11T10:00:00Z"),
        proposed_action=RobotAction("joint_move", (0.1,) * 6),
        safety_result=_safe_result(),
        backend_metadata={"name": "mock"},
        executed=True,
        sent_action=RobotAction("joint_move", (0.1,) * 6),
        execution_result=RuntimeExecutionResult(
            attempted=True,
            success=True,
            reason="executed",
            simulated=True,
            metadata={"execution_count": 1},
        ),
        blocked_reason=None,
    )

    step_path = recorder.record_step(result)

    metadata = json.loads((recorder.episode_dir / "metadata.json").read_text(encoding="utf-8"))
    lines = (recorder.episode_dir / "steps.jsonl").read_text(encoding="utf-8").splitlines()
    step = json.loads(lines[0])

    assert metadata["schema_version"] == "stage3.runtime_episode.v1"
    assert metadata["robot"] == "mock_realman_device"
    assert metadata["project_stage"] == "stage3_runtime_mvp"
    assert metadata["notes"] is None
    assert step_path == recorder.episode_dir / "steps.jsonl"
    assert step["episode_id"] == recorder.episode_id
    assert step["step_index"] == 1
    assert step["step_id"] == "step_000001"
    assert step["executed"] is True
    assert step["execution_result"]["success"] is True
    assert step["execution_result"]["metadata"]["execution_count"] == 1
    assert step["safety_result"]["decision"] == "approve"
