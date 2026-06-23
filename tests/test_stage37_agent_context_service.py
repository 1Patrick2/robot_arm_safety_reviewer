from pathlib import Path

from application.agent_context_service import AgentContextBuildRequest, build_agent_context

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


class TestBuildAgentContext:
    def test_builds_context_without_output_dir(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        result = build_agent_context(
            AgentContextBuildRequest(
                episode_id=ep_id,
                db_path=db_path,
            )
        )
        assert result.context.episode_id == ep_id
        assert result.context.total_steps == 2
        assert result.json_path is None
        assert result.markdown_path is None

    def test_builds_context_and_writes_files(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        result = build_agent_context(
            AgentContextBuildRequest(
                episode_id=ep_id,
                db_path=db_path,
                output_dir=tmp_path / "context",
            )
        )
        assert result.json_path is not None
        assert result.markdown_path is not None
        assert result.json_path.exists()
        assert result.markdown_path.exists()

    def test_to_dict(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        result = build_agent_context(
            AgentContextBuildRequest(
                episode_id=ep_id,
                db_path=db_path,
                output_dir=tmp_path / "context",
            )
        )
        d = result.to_dict()
        assert d["episode_id"] == ep_id
        assert d["critical_step_count"] >= 0
        assert d["json_path"] is not None
        assert d["markdown_path"] is not None

    def test_to_app_result_contains_artifacts(self, tmp_path):
        db_path, ep_id = _sandbox_and_ingest(tmp_path)
        result = build_agent_context(
            AgentContextBuildRequest(
                episode_id=ep_id,
                db_path=db_path,
                output_dir=tmp_path / "context",
            )
        )
        app = result.to_app_result()
        assert app.ok is True
        assert app.mode == "agent_context_build"
        kinds = [a.kind for a in app.artifacts]
        assert "diagnostic_context_json" in kinds
        assert "diagnostic_context_markdown" in kinds
