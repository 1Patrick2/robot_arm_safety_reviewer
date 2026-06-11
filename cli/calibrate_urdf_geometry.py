"""Generate URDF-vs-mock geometry calibration diagnostics.
CLI 包装器，用于运行 URDF 校准并输出结果。它接受一个任务目录作为输入，调用 calibrate_task_geometry 函数来执行校准，并根据用户的参数选择是否将完整的校准报告保存为 JSON 文件。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sim.urdf_calibration import calibrate_task_geometry

'''这个 CLI 脚本的主要功能是提供一个命令行接口，让用户能够方便地运行 URDF 校准过程，并查看校准结果。用户可以指定一个任务目录，脚本会调用 calibrate_task_geometry 函数来执行校准，并生成一个包含详细诊断信息的报告。用户还可以选择将这个报告保存为 JSON 文件，以便后续分析或记录。最后，脚本会在命令行上打印出校准的关键结果和结论，帮助用户快速了解 URDF 模型与 Mock 模型之间的几何差异和潜在问题。'''
def main() -> None:
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
