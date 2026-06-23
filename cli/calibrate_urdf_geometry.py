"""Generate URDF-vs-mock geometry calibration diagnostics.

CLI wrapper that accepts a task directory, runs ``calibrate_task_geometry``,
and optionally saves the full calibration report as JSON.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from diagnostics.geometry.urdf_calibration import calibrate_task_geometry


def main() -> None:
    """Parse args, run URDF calibration, and print the comparison report."""
    parser = argparse.ArgumentParser(description="Compare mock FK segments with PyBullet URDF collision geometry.")
    parser.add_argument("--task", required=True, help="Benchmark task directory")
    parser.add_argument("--output-json", help="Optional path for full calibration JSON")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation for --output-json")
    args = parser.parse_args()

    report = calibrate_task_geometry(args.task)
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=args.indent), encoding="utf-8")

    print("URDF Calibration")
    print(f"Task: {report['task_id']}")
    print(f"Worst Step: {report['worst_step']}")
    print(
        "PyBullet Closest: "
        f"link={report['pybullet']['closest_link']} "
        f"obstacle={report['pybullet']['closest_obstacle']} "
        f"clearance={report['pybullet']['clearance']}"
    )
    print(
        "Mock at PyBullet Worst Step: "
        f"link={report['mock_at_pybullet_worst_step']['closest_link']} "
        f"obstacle={report['mock_at_pybullet_worst_step']['closest_obstacle']} "
        f"clearance={report['mock_at_pybullet_worst_step']['clearance']}"
    )
    print(
        "Mock Overall Worst: "
        f"step={report['mock_overall_worst']['step']} "
        f"link={report['mock_overall_worst']['closest_link']} "
        f"obstacle={report['mock_overall_worst']['closest_obstacle']} "
        f"clearance={report['mock_overall_worst']['clearance']}"
    )
    print(f"Conclusion: {report['conclusion']['category']}")


if __name__ == "__main__":
    main()
