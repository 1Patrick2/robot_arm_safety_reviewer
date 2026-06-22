from pathlib import Path

from robot.runtime.scene_provider import StaticSceneProvider
from robot.runtime.types import RobotObservation


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_static_scene_provider_reads_scene_json():
    task_dir = BENCH / "simple_joint_move_001"
    provider = StaticSceneProvider(task_dir / "scene.json")
    observation = RobotObservation(
        robot_id="mock_realman_6dof",
        joint_positions=(0.0,) * 6,
        timestamp="2026-06-11T10:00:00Z",
    )

    scene = provider.get_scene(observation)

    assert provider.name == "static_scene"
    assert scene.scene_id == "simple_joint_move_001"
    assert len(scene.robot.joint_names) == 6
