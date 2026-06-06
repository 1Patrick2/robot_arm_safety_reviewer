"""Generate Markdown and optional 3D PNG report artifacts from an execution log."""

from __future__ import annotations

import argparse
from pathlib import Path

from reports.plot_3d import write_3d_plot
from reports.report_writer import write_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate robot arm safety report artifacts from a log.")
    parser.add_argument("--log", required=True, help="Path to execution log JSON")
    parser.add_argument("--output-dir", default="output_reports", help="Directory for Markdown and PNG reports")
    parser.add_argument("--skip-plot", action="store_true", help="Generate Markdown only")
    args = parser.parse_args()

    visualization_path = None
    if not args.skip_plot:
        try:
            visualization = write_3d_plot(args.log, args.output_dir)
            visualization_path = Path(visualization).name
            print(f"Visualization: {visualization}")
        except RuntimeError as exc:
            print(f"Visualization skipped: {exc}")

    report = write_markdown_report(args.log, args.output_dir, visualization_path=visualization_path)
    print(f"Markdown Report: {report}")


if __name__ == "__main__":
    main()
