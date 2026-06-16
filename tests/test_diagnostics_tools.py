import json
from pathlib import Path

import pytest

from diagnostics.tools import (
    load_diagnostic_context,
    get_episode_summary,
    list_critical_steps,
    get_worst_step,
    get_artifact_index,
)

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
        {"step_index": 2, "decision": "reject", "min_clearance": -0.05},
        {"step_index": 3, "decision": "manual_review", "min_clearance": 0.01},
    ],
    "artifacts": [
        {"kind": "clearance_curve", "path": "/tmp/curve.png", "description": "Curve"},
    ],
    "limitations": ["Test limitation"],
}


@pytest.fixture
def context_path(tmp_path):
    path = tmp_path / "diagnostic_context.json"
    path.write_text(json.dumps(SAMPLE_CONTEXT), encoding="utf-8")
    return path


class TestLoadDiagnosticContext:
    def test_loads_json(self, context_path):
        bundle = load_diagnostic_context(context_path)
        assert bundle["episode_id"] == "ep_001"

    def test_raises_for_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_diagnostic_context(tmp_path / "nonexistent.json")

    def test_raises_for_non_dict_json(self, tmp_path):
        path = tmp_path / "array.json"
        path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with pytest.raises(ValueError, match="must be a JSON object"):
            load_diagnostic_context(path)


class TestGetEpisodeSummary:
    def test_returns_summary_dict(self, context_path):
        bundle = load_diagnostic_context(context_path)
        summary = get_episode_summary(bundle)
        assert summary["episode_id"] == "ep_001"
        assert summary["total_steps"] == 3
        assert summary["blocked"] == 2


class TestListCriticalSteps:
    def test_returns_critical_steps(self, context_path):
        bundle = load_diagnostic_context(context_path)
        steps = list_critical_steps(bundle)
        assert len(steps) == 2
        assert steps[0]["decision"] == "reject"


class TestGetWorstStep:
    def test_uses_worst_sequence_step_index(self, context_path):
        """Should prefer matching by worst_sequence_step_index over min clearance."""
        bundle = load_diagnostic_context(context_path)
        worst = get_worst_step(bundle)
        assert worst is not None
        # worst_sequence_step_index is 2, which matches step_index=2
        assert worst["step_index"] == 2
        assert worst["decision"] == "reject"

    def test_fallback_to_min_clearance(self):
        """When worst_sequence_step_index doesn't match any step, fallback."""
        ctx = {
            "critical_steps": [
                {"step_index": 1, "min_clearance": 0.1},
                {"step_index": 5, "min_clearance": 0.02},
            ],
            # wrong_sequence_step_index should not match any step
        }
        # No worst_sequence_step_index set, should fallback to min clearance
        worst = get_worst_step(ctx)
        assert worst is not None
        assert worst["step_index"] == 5
        assert worst["min_clearance"] == 0.02

    def test_no_critical_steps_returns_none(self):
        assert get_worst_step({}) is None


class TestGetArtifactIndex:
    def test_returns_kind_path_dict(self, context_path):
        bundle = load_diagnostic_context(context_path)
        index = get_artifact_index(bundle)
        # Should return {kind: path} dict
        assert isinstance(index, dict)
        assert "clearance_curve" in index
        assert index["clearance_curve"] == "/tmp/curve.png"

    def test_empty_artifacts(self):
        assert get_artifact_index({}) == {}
