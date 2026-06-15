from pathlib import Path

from agent_context.builder import build_agent_context_from_db, _select_critical_steps
from agent_context.models import AgentContextStep

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "policy_sequences"
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
        assert len(ctx.artifacts) == 3
        assert len(ctx.critical_steps) > 0

    def test_context_includes_limitations(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        ctx = build_agent_context_from_db(db_path, ep_id)
        assert len(ctx.limitations) > 0
        assert any("deterministic safety reviewer" in l for l in ctx.limitations)

    def test_raises_for_missing_episode(self, tmp_path):
        db_path = tmp_path / "metrics.db"
        try:
            build_agent_context_from_db(db_path, "nonexistent")
            assert False, "expected KeyError"
        except KeyError:
            pass


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

    def test_empty_steps(self):
        selected = _select_critical_steps([])
        assert selected == []

    def test_deduplicates_same_step(self):
        steps = [
            {"step_index": 1, "safety_result": {"decision": "reject"}},
            {"step_index": 1, "safety_result": {"decision": "approve"}},
        ]
        selected = _select_critical_steps(steps)
        # reject wins, same step_index not duplicated
        assert len(selected) == 1
        assert selected[0].decision == "reject"
