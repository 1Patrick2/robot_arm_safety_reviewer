import json
import subprocess
import sys
from pathlib import Path

import pytest

from robot.safety.benchmark import run_benchmark, write_benchmark_summary_markdown
from robot.safety.scorer import validate_expected_schema

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench/sim_robot_arm"


def test_expected_files_follow_stage1_schema():
    for expected_path in BENCH.glob("*/expected.json"):
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

        validate_expected_schema(expected)


def test_stage1_benchmark_runner_scores_all_tasks(tmp_path):
    summary = run_benchmark(BENCH, log_dir=tmp_path / "logs")

    assert summary["total"] == 8
    assert summary["passed"] == 8
    assert summary["failed"] == 0
    assert summary["decision_accuracy"] == pytest.approx(1.0)
    assert summary["risk_accuracy"] == pytest.approx(1.0)
    assert summary["violation_match"] == pytest.approx(1.0)
    assert summary["gateway_execution_match"] == pytest.approx(1.0)
    assert len(list((tmp_path / "logs").glob("*/*.json"))) == 8


def test_benchmark_markdown_summary_is_written(tmp_path):
    summary = run_benchmark(BENCH, log_dir=tmp_path / "logs")

    path = write_benchmark_summary_markdown(summary, tmp_path / "benchmark_summary.md")

    text = path.read_text(encoding="utf-8")
    assert "Stage 1 Robot Safety Benchmark" in text
    assert "simple_joint_move_001" in text


def test_run_benchmark_cli_json_output(tmp_path):
    output_json = tmp_path / "summary.json"
    output_md = tmp_path / "summary.md"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.run_benchmark",
            "--bench",
            str(BENCH),
            "--log-dir",
            str(tmp_path / "logs"),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["total"] == 8
    assert payload["passed"] == 8
    assert output_json.exists()
    assert output_md.exists()
