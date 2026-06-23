import json
from pathlib import Path

from diagnostics.report.runtime_episode_report import (
    build_runtime_episode_markdown,
    write_runtime_episode_report,
)
from robot.runtime.episode_loader import RuntimeEpisodeBundle


def _make_bundle(*, steps_data: list[dict] | None = None) -> RuntimeEpisodeBundle:
    meta = {
        "episode_id": "test_ep_001",
        "backend": "mock",
        "robot": "mock_realman",
        "action_source": "replay",
        "scene_provider": "static_scene",
    }
    steps = steps_data or [
        {
            "step_id": "step_000001",
            "observation": {"robot_id": "mock_realman_6dof", "joint_positions": [0, 0, 0, 0, 0, 0], "timestamp": "2026-01-01T00:00:00Z", "metadata": {}},
            "proposed_action": {"action_type": "joint_move", "target_joints": [0.1, 0.1, 0, 0, 0, 0], "speed": 0.1, "source": "replay", "metadata": {}},
            "safety_result": {"decision": "approve", "risk_level": "low", "min_clearance": 0.05, "closest_robot_link": None, "closest_obstacle": None},
            "executed": True,
            "blocked_reason": None,
        },
        {
            "step_id": "step_000002",
            "observation": {"robot_id": "mock_realman_6dof", "joint_positions": [0.1, 0.1, 0, 0, 0, 0], "timestamp": "2026-01-01T00:01:00Z", "metadata": {}},
            "proposed_action": {"action_type": "joint_move", "target_joints": [0.4, 0.2, 0.1, 0, 0, 0], "speed": 0.1, "source": "replay", "metadata": {}},
            "safety_result": {"decision": "manual_review", "risk_level": "medium", "min_clearance": 0.01, "closest_robot_link": "link_3", "closest_obstacle": "sphere_01"},
            "executed": False,
            "blocked_reason": "manual_review_required",
        },
    ]
    return RuntimeEpisodeBundle(
        episode_dir=Path("/tmp/fake"),
        metadata=meta,
        steps=tuple(steps),
    )


class TestBuildRuntimeEpisodeMarkdown:
    def test_contains_overview_section(self):
        bundle = _make_bundle()
        md = build_runtime_episode_markdown(bundle)
        assert "# Runtime Episode Summary" in md
        assert "## Overview" in md
        assert "test_ep_001" in md
        assert "mock" in md

    def test_contains_step_table(self):
        bundle = _make_bundle()
        md = build_runtime_episode_markdown(bundle)
        assert "## Step Table" in md
        assert "step_000001" in md
        assert "step_000002" in md
        assert "approve" in md
        assert "manual_review" in md

    def test_contains_artifacts_section(self):
        bundle = _make_bundle()
        md = build_runtime_episode_markdown(bundle)
        assert "## Artifacts" in md
        assert "steps.jsonl" in md
        assert "metadata.json" in md

    def test_counts_mixed_decisions(self):
        # 2 approve, 1 reject = 3 steps
        steps = [
            {"step_id": "s1", "safety_result": {"decision": "approve"}, "executed": True, "blocked_reason": None},
            {"step_id": "s2", "safety_result": {"decision": "approve"}, "executed": True, "blocked_reason": None},
            {"step_id": "s3", "safety_result": {"decision": "reject"}, "executed": False, "blocked_reason": "rejected_by_safety_gate"},
        ]
        bundle = _make_bundle(steps_data=steps)
        md = build_runtime_episode_markdown(bundle)
        assert "- Total Steps: 3" in md
        assert "- Approved: 2" in md
        assert "- Executed: 2" in md
        assert "- Blocked: 1" in md
        assert "- Rejected: 1" in md


class TestWriteRuntimeEpisodeReport:
    def test_writes_markdown_file(self, tmp_path):
        ep_dir = tmp_path / "episode_001"
        ep_dir.mkdir()
        (ep_dir / "metadata.json").write_text(
            json.dumps({"episode_id": "ep_001", "backend": "mock", "robot": "mr"}),
            encoding="utf-8",
        )
        with (ep_dir / "steps.jsonl").open("w") as f:
            f.write(json.dumps({"step_id": "s1", "safety_result": {"decision": "approve"}, "executed": True, "blocked_reason": None}) + "\n")

        report_path = write_runtime_episode_report(ep_dir)
        assert report_path.exists()
        text = report_path.read_text(encoding="utf-8")
        assert "# Runtime Episode Summary" in text
        assert "ep_001" in text
