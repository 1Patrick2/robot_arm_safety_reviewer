import json
import subprocess
import sys
from pathlib import Path

import pytest

from application.gateway.safety_gate import review_only
from diagnostics.report.plot_3d import write_3d_plot
from diagnostics.report.report_writer import build_markdown_report, write_markdown_report

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench/sim_robot_arm"


def _log_payload(tmp_path):
    task_dir = BENCH / "obstacle_collision_001"
    outcome = review_only(task_dir / "scene.json", task_dir / "command.json", log_dir=tmp_path)
    return outcome.execution_log, outcome.log_path


def test_build_markdown_report_includes_core_sections(tmp_path):
    payload, _ = _log_payload(tmp_path)

    markdown = build_markdown_report(payload)

    assert "# Robot Arm Safety Review Report" in markdown
    assert "## Safety Checks" in markdown
    assert "## Gate Decision" in markdown
    assert "## Recommended Action" in markdown
    assert "Decision: `reject`" in markdown
    assert "sphere_01" in markdown
    assert "Do not execute this command." in markdown


def test_markdown_report_marks_no_obstacle_clearance_not_applicable(tmp_path):
    task_dir = BENCH / "simple_joint_move_001"
    outcome = review_only(task_dir / "scene.json", task_dir / "command.json", log_dir=tmp_path)

    markdown = build_markdown_report(outcome.execution_log)

    assert "N/A - no obstacles" in markdown
    assert "NOT_CHECKED" in markdown


def test_write_markdown_report_creates_file(tmp_path):
    _, log_path = _log_payload(tmp_path)

    report_path = write_markdown_report(log_path, tmp_path)

    assert report_path.exists()
    assert "Robot Arm Safety Review Report" in report_path.read_text(encoding="utf-8")


def test_write_3d_plot_creates_png_when_matplotlib_available(tmp_path):
    pytest.importorskip("matplotlib")
    _, log_path = _log_payload(tmp_path)

    png_path = write_3d_plot(log_path, tmp_path)

    assert png_path.exists()
    assert png_path.suffix == ".png"


def test_generate_report_cli_markdown_only(tmp_path):
    _, log_path = _log_payload(tmp_path)
    output_dir = tmp_path / "reports"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.generate_report",
            "--log",
            str(log_path),
            "--output-dir",
            str(output_dir),
            "--skip-plot",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Markdown Report:" in completed.stdout
    reports = list(output_dir.glob("*.md"))
    assert reports
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert reports[0].stem == payload["log_id"]
