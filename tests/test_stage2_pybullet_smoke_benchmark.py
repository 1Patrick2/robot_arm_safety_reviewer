import json
import subprocess
import sys
from pathlib import Path

import pytest

from robot.safety.benchmark import run_backend_smoke_benchmark


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_pybullet_smoke_benchmark_runs_all_tasks_with_structured_outputs(tmp_path):
    pytest.importorskip("pybullet")

    summary = run_backend_smoke_benchmark(BENCH, backend_name="pybullet", log_dir=tmp_path / "logs")

    assert summary["backend"] == "pybullet"
    assert summary["mode"] == "smoke"
    assert summary["total"] == 8
    assert summary["completed"] == 8
    assert summary["runtime_errors"] == 0
    assert summary["structured_outputs"] == 8
    assert len(summary["tasks"]) == 8
    assert len(list((tmp_path / "logs").glob("*/*.json"))) == 8
    for task in summary["tasks"]:
        assert task["completed"] is True
        assert task["structured_output"] is True
        assert task["decision"] in {"approve", "manual_review", "reject"}
        assert task["risk_level"] in {"low", "medium", "high"}
        assert task["review_backend"]["name"] == "pybullet"
        assert task["evidence_count"] > 0


def test_run_benchmark_cli_smoke_mode_outputs_json(tmp_path):
    pytest.importorskip("pybullet")
    output_json = tmp_path / "pybullet_smoke.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.run_benchmark",
            "--backend",
            "pybullet",
            "--mode",
            "smoke",
            "--bench",
            str(BENCH),
            "--log-dir",
            str(tmp_path / "logs"),
            "--output-json",
            str(output_json),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["backend"] == "pybullet"
    assert payload["mode"] == "smoke"
    assert payload["completed"] == 8
    assert output_json.exists()


def test_run_benchmark_cli_smoke_mode_writes_markdown(tmp_path):
    pytest.importorskip("pybullet")
    output_md = tmp_path / "pybullet_smoke.md"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.run_benchmark",
            "--backend",
            "pybullet",
            "--mode",
            "smoke",
            "--bench",
            str(BENCH),
            "--log-dir",
            str(tmp_path / "logs"),
            "--output-md",
            str(output_md),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Smoke Passed: True" in completed.stdout
    assert "Structured Outputs: 8" in completed.stdout
    assert output_md.exists()
    markdown = output_md.read_text(encoding="utf-8")
    assert "# Backend Smoke Benchmark" in markdown
    assert "simple_joint_move_001" in markdown
