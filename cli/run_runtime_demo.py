from __future__ import annotations

import argparse
import json
from pathlib import Path

from robot_runtime.action_source import ReplayActionSource
from robot_runtime.adapters.mock_realman_device import MockRealManDevice
from robot_runtime.episode_recorder import EpisodeRecorder
from robot_runtime.safety_runtime import SafetyRuntime
from robot_runtime.scene_provider import StaticSceneProvider
from sim.backend_factory import create_backend


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Stage 3 runtime MVP demo task.")
    parser.add_argument("--task", required=True, help="Benchmark task directory containing scene.json and command.json")
    parser.add_argument("--backend", default="mock", choices=("mock", "pybullet"))
    parser.add_argument("--episode-dir", default="output_reports/runtime_demo")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    task_dir = Path(args.task)
    scene_path = task_dir / "scene.json"
    command_path = task_dir / "command.json"
    if not scene_path.exists():
        parser.error(f"scene.json not found: {scene_path}")
    if not command_path.exists():
        parser.error(f"command.json not found: {command_path}")

    action_source = ReplayActionSource(command_path)
    scene_provider = StaticSceneProvider(scene_path)
    initial_joints = action_source.command.current_joints
    robot = MockRealManDevice(initial_joints=initial_joints)
    backend = create_backend(args.backend)
    recorder = EpisodeRecorder(
        root_dir=args.episode_dir,
        robot_name=robot.name,
        action_source_name=action_source.name,
        scene_provider_name=scene_provider.name,
        backend_name=args.backend,
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
        result = runtime.step()
    finally:
        robot.disconnect()

    payload = {
        "task": str(task_dir),
        "backend": args.backend,
        "episode_dir": str(recorder.episode_dir),
        "result": result.to_dict(),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(f"Decision: {result.safety_result.decision}")
    print(f"Risk Level: {result.safety_result.risk_level}")
    print(f"Executed: {result.executed}")
    print(f"Blocked Reason: {result.blocked_reason}")
    print(f"Episode Dir: {recorder.episode_dir}")
    print(f"Episode Step Path: {result.episode_step_path}")


if __name__ == "__main__":
    main()
