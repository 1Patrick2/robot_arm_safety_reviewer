from __future__ import annotations

import argparse
from pathlib import Path

from application.runtime_service import RuntimeTaskRequest, run_runtime_task
from cli.output import print_runtime_task_result


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

    print_runtime_task_result(runtime_result, as_json=args.json)


if __name__ == "__main__":
    main()
