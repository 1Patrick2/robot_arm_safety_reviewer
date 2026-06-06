import json
import subprocess
import sys
from pathlib import Path

import pytest

from reports.backend_comparison import compare_backends


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_compare_backends_runs_mock_and_pybullet_with_diagnostics(tmp_path):
    pytest.importorskip("pybullet")

    summary = compare_backends(
        BENCH,
        backends=("mock", "pybullet"),
        log_dir=tmp_path / "logs",
    )

    assert summary["backends"] == ["mock", "pybullet"]
    assert summary["total"] == 8
    assert summary["backend_errors"] == 0
    assert "decision_matches" in summary
    assert "risk_matches" in summary
    assert len(summary["tasks"]) == 8

    first = summary["tasks"][0]
    assert set(first["results"]) == {"mock", "pybullet"}
    assert first["match_status"] in {
        "decision_match",
        "decision_mismatch",
        "risk_mismatch",
        "clearance_band_mismatch",
        "attribution_mismatch",
        "backend_error",
    }
    assert first["diagnosis"]
    assert "decision" in first["results"]["mock"]
    assert "decision" in first["results"]["pybullet"]


def test_compare_backends_cli_writes_json_and_markdown(tmp_path):
    pytest.importorskip("pybullet")
    output_json = tmp_path / "backend_comparison.json"
    output_md = tmp_path / "backend_comparison.md"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.compare_backends",
            "--bench",
            str(BENCH),
            "--backends",
            "mock",
            "pybullet",
            "--log-dir",
            str(tmp_path / "logs"),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Backend Comparison" in completed.stdout
    assert output_json.exists()
    assert output_md.exists()

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")
    assert payload["total"] == 8
    assert "# Backend Comparison Report" in markdown
    assert "simple_joint_move_001" in markdown
