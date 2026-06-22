from pathlib import Path

from robot.runtime.action_source import ReplayActionSource


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_replay_action_source_reads_command_json():
    task_dir = BENCH / "simple_joint_move_001"
    source = ReplayActionSource(task_dir / "command.json")
    observation = object()

    action = source.propose_action(observation)

    assert source.name == "replay"
    assert action.action_type == "joint_move"
    assert action.source == "replay"
    assert action.metadata["command_id"] == "cmd_simple_safe_001"
    assert len(action.target_joints) == 6
