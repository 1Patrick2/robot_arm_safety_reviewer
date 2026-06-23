from pathlib import Path

import json

import pytest

from diagnostics.context.builder import (
    _normalise_step,
    build_agent_context_from_db,
    _select_critical_steps,
)
from diagnostics.context.models import AgentContextStep

SAMPLES = Path(__file__).resolve().parents[1] / "bench" / "samples" / "policy_sequences"
BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"


def _sandbox_and_ingest(tmp_path) -> tuple[Path, str]:
    """Run sandbox with metrics-db and return (db_path, episode_id)."""
    from application.sandbox_service import SandboxRunRequest, run_sandbox  # noqa: PLC0415

    db_path = tmp_path / "metrics.db"
    result = run_sandbox(
        SandboxRunRequest(
            sequence_path=SAMPLES / "simple_safe_sequence.json",
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            output_root=tmp_path / "sandbox",
            metrics_db=db_path,
        )
    )
    ep_id = result.sequence_runtime_result.episode_dir.name
    return db_path, ep_id


class TestBuildAgentContextFromDb:
    def test_builds_context_for_ingested_episode(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        ctx = build_agent_context_from_db(db_path, ep_id)
        assert ctx.episode_id == ep_id
        assert ctx.total_steps == 2
        assert ctx.approved_steps == 2
        assert ctx.executed_steps == 2
        assert ctx.min_clearance is not None
        assert len(ctx.artifacts) == 4
        assert len(ctx.critical_steps) > 0

    def test_context_includes_limitations(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        ctx = build_agent_context_from_db(db_path, ep_id)
        assert len(ctx.limitations) > 0
        assert any("deterministic safety reviewer" in l for l in ctx.limitations)

    def test_raises_for_missing_episode(self, tmp_path):
        db_path = tmp_path / "metrics.db"
        with pytest.raises(KeyError):
            build_agent_context_from_db(db_path, "nonexistent")

    def test_run_mode_from_metadata(self, tmp_path):
        """Verify run_mode is populated from the stored metadata_json."""
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        ctx = build_agent_context_from_db(db_path, ep_id)
        assert ctx.run_mode == "sandbox"


class TestBuildAgentContextFromDbCriticalSteps:
    """Test that DB rows yield correct reject/manual_review decisions."""

    def _ingest_with_reject(self, tmp_path) -> tuple[Path, str]:
        """Run a near-miss sequence (produces manual_review)."""
        from application.sandbox_service import SandboxRunRequest, run_sandbox

        db_path = tmp_path / "metrics.db"
        result = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "near_miss_sequence.json",
                scene_path=BENCH / "near_miss_clearance_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path / "reject_sandbox",
                metrics_db=db_path,
            )
        )
        ep_id = result.sequence_runtime_result.episode_dir.name
        return db_path, ep_id

    def test_reject_steps_have_correct_decision_from_db(self, tmp_path):
        """Real DB rows should preserve reject/manual_review decisions."""
        db_path, ep_id = self._ingest_with_reject(tmp_path)
        ctx = build_agent_context_from_db(db_path, ep_id)
        assert ctx.total_steps > 0
        assert ctx.blocked_steps > 0
        # At least one critical step should be non-approve
        non_approve = [s for s in ctx.critical_steps if s.decision != "approve"]
        assert len(non_approve) > 0, (
            f"expected non-approve critical steps, got decisions="
            f"{[s.decision for s in ctx.critical_steps]}"
        )


class TestNormaliseStep:
    def test_passes_through_rich_step(self):
        step = {"step_index": 1, "safety_result": {"decision": "reject", "min_clearance": -0.05}}
        result = _normalise_step(step)
        assert result is step  # same object

    def test_parses_safety_result_json(self):
        step = {
            "step_index": 1,
            "decision": "reject",
            "risk_level": "high",
            "min_clearance": -0.05,
            "safety_result_json": json.dumps(
                {"decision": "reject", "risk_level": "high", "min_clearance": -0.05}
            ),
        }
        result = _normalise_step(step)
        sr = result["safety_result"]
        assert sr["decision"] == "reject"
        assert sr["min_clearance"] == -0.05

    def test_falls_back_to_top_level_columns(self):
        step = {
            "step_index": 1,
            "decision": "reject",
            "risk_level": "high",
            "min_clearance": -0.05,
            "closest_robot_link": "link_3",
            "closest_obstacle": "sphere_01",
            "worst_step": 7,
        }
        result = _normalise_step(step)
        sr = result["safety_result"]
        assert sr["decision"] == "reject"
        assert sr["min_clearance"] == -0.05
        assert sr["closest_robot_link"] == "link_3"

    def test_empty_step_returns_empty_safety_result(self):
        result = _normalise_step({})
        assert result["safety_result"] == {
            "decision": None,
            "risk_level": None,
            "min_clearance": None,
            "closest_robot_link": None,
            "closest_obstacle": None,
            "worst_step": None,
        }

    def test_parses_proposed_action_json(self):
        step = {
            "step_index": 1,
            "proposed_action_json": json.dumps(
                {"action_type": "joint_move", "target_joints": [0.1, 0.2, 0.0, 0.0, 0.0, 0.0]}
            ),
        }
        result = _normalise_step(step)
        pa = result["proposed_action"]
        assert pa.get("action_type") == "joint_move"
        assert len(pa.get("target_joints", [])) == 6

    def test_keeps_existing_proposed_action_over_json(self):
        step = {
            "step_index": 1,
            "proposed_action": {"action_type": "joint_move", "target_joints": [0.1] * 6},
            "proposed_action_json": json.dumps({"action_type": "wrong"}),
        }
        result = _normalise_step(step)
        assert result["proposed_action"]["action_type"] == "joint_move"


class TestSelectCriticalSteps:
    def test_reject_steps_first(self):
        steps = [
            {"step_index": 1, "safety_result": {"decision": "approve", "min_clearance": 0.1}},
            {"step_index": 2, "safety_result": {"decision": "reject", "min_clearance": -0.05}},
            {"step_index": 3, "safety_result": {"decision": "manual_review", "min_clearance": 0.01}},
        ]
        selected = _select_critical_steps(steps)
        decisions = [s.decision for s in selected]
        assert decisions == ["reject", "manual_review", "approve"]

    def test_lower_clearance_first_within_group(self):
        steps = [
            {"step_index": 1, "safety_result": {"decision": "approve", "min_clearance": 0.1}},
            {"step_index": 2, "safety_result": {"decision": "approve", "min_clearance": 0.05}},
        ]
        selected = _select_critical_steps(steps, max_steps=10)
        assert selected[0].min_clearance == 0.05

    def test_max_steps_respected(self):
        steps = [
            {"step_index": i, "safety_result": {"decision": "approve", "min_clearance": 0.1}}
            for i in range(1, 21)
        ]
        selected = _select_critical_steps(steps, max_steps=5)
        assert len(selected) == 5

    def test_zero_min_clearance_not_treated_as_missing(self):
        """0.0 clearance is a contact boundary, not absent data."""
        steps = [
            {"step_index": 1, "safety_result": {"decision": "manual_review", "min_clearance": 0.0}},
            {"step_index": 2, "safety_result": {"decision": "approve", "min_clearance": 0.1}},
        ]
        selected = _select_critical_steps(steps)
        assert selected[0].min_clearance == 0.0

    def test_none_clearance_sorted_last(self):
        steps = [
            {"step_index": 1, "safety_result": {"decision": "approve", "min_clearance": None}},
            {"step_index": 2, "safety_result": {"decision": "approve", "min_clearance": 0.05}},
        ]
        selected = _select_critical_steps(steps, max_steps=10)
        # step 2 (clearance 0.05) should come first
        assert selected[0].min_clearance == 0.05

    def test_empty_steps(self):
        selected = _select_critical_steps([])
        assert selected == []

    def test_deduplicates_same_step(self):
        steps = [
            {"step_index": 1, "safety_result": {"decision": "reject"}},
            {"step_index": 1, "safety_result": {"decision": "approve"}},
        ]
        selected = _select_critical_steps(steps)
        assert len(selected) == 1
        assert selected[0].decision == "reject"

    def test_db_row_reject_preserved(self):
        """DB-style rows (flat columns with safety_result_json) should preserve reject."""
        step = {
            "step_index": 1,
            "decision": "reject",
            "risk_level": "high",
            "min_clearance": -0.05,
            "closest_robot_link": "link_2",
            "closest_obstacle": "sphere_01",
            "worst_step": 0,
            "safety_result_json": json.dumps(
                {"decision": "reject", "risk_level": "high", "min_clearance": -0.05,
                 "closest_robot_link": "link_2", "closest_obstacle": "sphere_01", "worst_step": 0}
            ),
        }
        selected = _select_critical_steps([step])
        assert len(selected) == 1
        assert selected[0].decision == "reject"
        assert selected[0].min_clearance == -0.05
        assert selected[0].closest_robot_link == "link_2"
        assert selected[0].closest_obstacle == "sphere_01"
        assert selected[0].backend_worst_step == 0
