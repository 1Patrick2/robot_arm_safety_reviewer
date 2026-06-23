"""Compare benchmark outputs across simulation backends.

Parses --bench, --backends, --log-dir, --output-json, --output-md CLI arguments,
runs the backend comparison, and writes results to JSON and/or Markdown files.
"""

from __future__ import annotations

import argparse

from diagnostics.report.backend_comparison import (
    compare_backends,
    write_backend_comparison_json,
    write_backend_comparison_markdown,
)


def main() -> None:
    """Parse args, compare backends, write output files, and print summary."""
    parser = argparse.ArgumentParser(description="Compare robot arm safety outputs across backends.")
    parser.add_argument("--bench", default="bench/sim_robot_arm", help="Benchmark root directory")
    parser.add_argument("--backends", nargs="+", default=["mock", "pybullet"], help="Backends to compare")
    parser.add_argument("--log-dir", default="logs/backend_comparison", help="Directory for per-backend logs")
    parser.add_argument("--output-json", help="Optional path for comparison JSON")
    parser.add_argument("--output-md", help="Optional path for comparison Markdown")
    args = parser.parse_args()

    summary = compare_backends(args.bench, backends=args.backends, log_dir=args.log_dir)
    if args.output_json:
        write_backend_comparison_json(summary, args.output_json)
    if args.output_md:
        write_backend_comparison_markdown(summary, args.output_md)

    print("Backend Comparison")
    print(f"Backends: {', '.join(summary['backends'])}")
    print(f"Tasks: {summary['total']}")
    print(f"Decision Matches: {summary['decision_matches']}")
    print(f"Risk Matches: {summary['risk_matches']}")
    print(f"Clearance Band Matches: {summary['clearance_band_matches']}")
    print(f"Attribution Matches: {summary['attribution_matches']}")
    print(f"Strict Matches: {summary['strict_matches']}")
    print(f"Backend Errors: {summary['backend_errors']}")


if __name__ == "__main__":
    main()
