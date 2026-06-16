import json
from pathlib import Path

import pytest

from diagnostics.report import build_diagnostic_report

SAMPLE_CONTEXT = {
    "episode_id": "ep_001",
    "sequence_id": "seq_001",
    "backend": "mock",
    "total_steps": 3,
    "approved_steps": 1,
    "executed_steps": 1,
    "blocked_steps": 2,
    "rejected_steps": 1,
    "manual_review_steps": 1,
    "min_clearance": -0.05,
    "worst_sequence_step_index": 2,
    "critical_steps": [
        {"step_index": 2, "decision": "reject", "risk_level": "high",
         "min_clearance": -0.05, "closest_robot_link": "link_3",
         "closest_obstacle": "sphere_01"},
        {"step_index": 3, "decision": "manual_review", "risk_level": "medium",
         "min_clearance": 0.01, "closest_robot_link": "link_2",
         "closest_obstacle": "sphere_01"},
    ],
    "artifacts": [
        {"kind": "clearance_curve", "path": "/tmp/curve.png", "description": "Clearance curve"},
    ],
    "limitations": ["This project is a deterministic safety reviewer, not a planner."],
}


@pytest.fixture
def bundle():
    return SAMPLE_CONTEXT


class TestBuildDiagnosticReport:
    def test_report_contains_episode_id(self, bundle):
        report = build_diagnostic_report(bundle)
        assert "ep_001" in report

    def test_report_contains_safety_summary(self, bundle):
        report = build_diagnostic_report(bundle)
        assert "## Safety Summary" in report
        assert "Total Steps: 3" in report
        assert "Rejected: 1" in report

    def test_report_contains_worst_step_analysis(self, bundle):
        report = build_diagnostic_report(bundle)
        assert "## Worst Step Analysis" in report
        assert "reject" in report
        assert "-0.05" in report

    def test_report_contains_critical_step_table(self, bundle):
        report = build_diagnostic_report(bundle)
        assert "## Critical Step Table" in report
        assert "link_3" in report

    def test_report_contains_artifact_references(self, bundle):
        report = build_diagnostic_report(bundle)
        assert "## Artifact References" in report
        assert "clearance_curve" in report

    def test_report_contains_deterministic_boundary(self, bundle):
        report = build_diagnostic_report(bundle)
        assert "Deterministic Safety Boundary" in report
        assert "planner" in report

    def test_report_contains_human_review_focus(self, bundle):
        report = build_diagnostic_report(bundle)
        assert "## Human Review Focus" in report
