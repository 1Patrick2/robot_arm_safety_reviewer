"""Generate PyBullet geometry diagnostics for one benchmark task.
诊断CLI命令，把diagnose_task_geometry.py包装成cli命令，支持参数--task, --output-json, --include-base-collision, --search-distance, --indent等，方便在命令行执行PyBullet几何诊断，并输出结果到json文件中。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from robot.backends.pybullet_backend import DEFAULT_CLOSEST_POINT_DISTANCE, PyBulletBackend
from sim.pybullet_diagnostics import diagnose_task_geometry


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate PyBullet geometry diagnostics for a benchmark task.")
    parser.add_argument("--task", required=True, help="Benchmark task directory")
    parser.add_argument("--output-json", help="Optional path for full diagnostic JSON")
    parser.add_argument("--include-base-collision", action="store_true", help="Include PyBullet base link in queries")
    parser.add_argument(
        "--search-distance",
        type=float,
        default=DEFAULT_CLOSEST_POINT_DISTANCE,
        help="PyBullet getClosestPoints search distance",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation for --output-json")
    args = parser.parse_args()

    backend = PyBulletBackend(
        closest_point_search_distance=args.search_distance,
        include_base_collision=args.include_base_collision,
    )
    diagnostic = diagnose_task_geometry(args.task, backend=backend)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(diagnostic, ensure_ascii=False, indent=args.indent), encoding="utf-8")

    worst_pair = diagnostic["worst_pair"]
    print("Geometry Diagnostics")
    print(f"Task: {diagnostic['task_id']}")
    print(f"Backend: {diagnostic['backend']}")
    print(f"Collision Method: {diagnostic['collision_method']}")
    print(
        "Worst Pair: "
        f"step={worst_pair['step']} "
        f"link={worst_pair['robot_link']} "
        f"obstacle={worst_pair['obstacle']} "
        f"clearance={worst_pair['clearance']}"
    )


if __name__ == "__main__":
    main()
