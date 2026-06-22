"""Run the Stage 1 simulated robot arm benchmark."""

from __future__ import annotations

import argparse
import json

from robot.safety.benchmark import (
    run_backend_smoke_benchmark,
    run_benchmark,
    write_backend_smoke_summary_markdown,
    write_benchmark_summary_json,
    write_benchmark_summary_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run and score the Stage 1 robot arm safety benchmark.")
    parser.add_argument("--bench", default="bench/sim_robot_arm", help="Benchmark root directory")
    parser.add_argument(
        "--backend", default="mock", choices=["mock", "pybullet"], help="Simulation backend for safety review"
    )
    parser.add_argument("--mode", default="scored", choices=["scored", "smoke"], help="Benchmark scoring mode")
    parser.add_argument("--log-dir", default="logs/benchmark", help="Directory for per-task execution logs")
    parser.add_argument("--output-json", help="Optional path for benchmark summary JSON")
    parser.add_argument("--output-md", help="Optional path for benchmark summary Markdown")
    parser.add_argument("--json", action="store_true", help="Print the full benchmark summary JSON")
    args = parser.parse_args()

    if args.mode == "smoke":
        summary = run_backend_smoke_benchmark(args.bench, backend_name=args.backend, log_dir=args.log_dir)
    else:
        summary = run_benchmark(args.bench, backend_name=args.backend, log_dir=args.log_dir)
    if args.output_json:
        write_benchmark_summary_json(summary, args.output_json)
    if args.output_md:
        if args.mode == "smoke":
            write_backend_smoke_summary_markdown(summary, args.output_md)
        else:
            write_benchmark_summary_markdown(summary, args.output_md)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    print(f"Total: {summary['total']}")
    if args.mode == "smoke":
        print(f"Smoke Passed: {summary['passed']}")
        print(f"Completed: {summary['completed']}")
        print(f"Runtime Errors: {summary['runtime_errors']}")
        print(f"Structured Outputs: {summary['structured_outputs']}")
        return

    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Decision Accuracy: {summary['decision_accuracy']:.3f}")
    print(f"Risk Accuracy: {summary['risk_accuracy']:.3f}")
    print(f"Violation Match: {summary['violation_match']:.3f}")
    print(f"Gateway Execution Match: {summary['gateway_execution_match']:.3f}")


if __name__ == "__main__":
    main()
