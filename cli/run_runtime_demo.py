from __future__ import annotations

import argparse
import json
from pathlib import Path

from application.runtime_service import RuntimeTaskRequest, run_runtime_task


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Stage 3 runtime MVP demo task.")
    parser.add_argument("--task", required=True, help="Benchmark task directory containing scene.json and command.json")
    parser.add_argument("--backend", default="mock", choices=("mock", "pybullet"))
    parser.add_argument("--episode-dir", default="output_reports/runtime_demo")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        runtime_result = run_runtime_task(
            RuntimeTaskRequest(
                task_dir=Path(args.task),
                backend_name=args.backend,
                episode_root=Path(args.episode_dir),
            )
        )
    except FileNotFoundError as exc:
        parser.error(str(exc))

    result = runtime_result.step_result
    payload = runtime_result.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(f"Decision: {result.safety_result.decision}")
    print(f"Risk Level: {result.safety_result.risk_level}")
    print(f"Executed: {result.executed}")
    print(f"Blocked Reason: {result.blocked_reason}")
    print(f"Episode Dir: {runtime_result.episode_dir}")
    print(f"Episode Step Path: {result.episode_step_path}")


if __name__ == "__main__":
    main()
