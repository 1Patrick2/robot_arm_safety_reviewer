import json
from pathlib import Path

import pytest

from reports.runtime_visual_report import write_clearance_curve


def _write_test_episode(episode_dir: Path) -> Path:
    episode_dir.mkdir(parents=True)
    (episode_dir / "metadata.json").write_text(
        json.dumps({"episode_id": "test_ep", "backend": "mock", "robot": "mock_realman"}),
        encoding="utf-8",
    )
    steps = [
        {
            "step_id": "step_000001",
            "safety_result": {"decision": "approve", "risk_level": "low", "min_clearance": 0.10},
            "executed": True,
            "blocked_reason": None,
        },
        {
            "step_id": "step_000002",
            "safety_result": {"decision": "approve", "risk_level": "low", "min_clearance": 0.05},
            "executed": True,
            "blocked_reason": None,
        },
        {
            "step_id": "step_000003",
            "safety_result": {"decision": "manual_review", "risk_level": "medium", "min_clearance": 0.01},
            "executed": False,
            "blocked_reason": "manual_review_required",
        },
    ]
    with (episode_dir / "steps.jsonl").open("w", encoding="utf-8") as f:
        for s in steps:
            f.write(json.dumps(s) + "\n")
    return episode_dir


class TestWriteClearanceCurve:
    def test_creates_png_file(self, tmp_path):
        ep_dir = _write_test_episode(tmp_path / "ep_001")
        plot_path = write_clearance_curve(ep_dir)
        assert plot_path.exists()
        assert plot_path.suffix == ".png"
        assert plot_path.stat().st_size > 0

    def test_accepts_custom_output_dir(self, tmp_path):
        ep_dir = _write_test_episode(tmp_path / "ep_002")
        out_dir = tmp_path / "output"
        plot_path = write_clearance_curve(ep_dir, output_dir=out_dir)
        assert plot_path.parent == out_dir
        assert plot_path.exists()

    def test_raises_for_missing_episode(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            write_clearance_curve(tmp_path / "nonexistent")
