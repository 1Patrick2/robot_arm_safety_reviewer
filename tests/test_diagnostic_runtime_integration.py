"""End-to-end integration test for the full diagnostic runtime pipeline.

Covers: sandbox run -> metrics DB -> context build -> diagnostics tools
      -> diagnostic report -> fake diagnostic agent report

No DeepSeek API key required.
"""
import json
from pathlib import Path

from application.sandbox_service import SandboxRunRequest, run_sandbox
from application.agent_context_service import AgentContextBuildRequest, build_agent_context
from diagnostics.tools.context_tools import load_diagnostic_context, get_episode_summary, get_worst_step, list_critical_steps, get_artifact_index
from diagnostics.report.deterministic import build_diagnostic_report
from diagnostics.agent.runner import run_diagnostic_agent

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "policy_sequences"
BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"


class TestDiagnosticRuntimeIntegration:
    def test_full_pipeline_with_fake_agent(self, tmp_path):
        """sandbox -> metrics DB -> agent context -> diagnostics -> report -> fake agent."""

        # 1. sandbox run with metrics-db
        metrics_db = tmp_path / "runtime_metrics.db"
        sandbox_result = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "simple_safe_sequence.json",
                scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                backend_name="mock",
                output_root=tmp_path / "sandbox",
                metrics_db=metrics_db,
            )
        )
        episode_dir = sandbox_result.sequence_runtime_result.episode_dir
        assert episode_dir.exists()
        assert sandbox_result.sequence_runtime_result.total_steps == 2

        # 2. build agent context
        ctx_result = build_agent_context(
            AgentContextBuildRequest(
                episode_id=episode_dir.name,
                db_path=metrics_db,
                output_dir=tmp_path / "agent_context",
            )
        )
        assert ctx_result.json_path is not None
        assert ctx_result.json_path.exists()
        assert ctx_result.context.episode_id == episode_dir.name

        # 3. load diagnostic context
        bundle = load_diagnostic_context(ctx_result.json_path)
        assert bundle["episode_id"] == episode_dir.name

        # 4. diagnostics tools
        summary = get_episode_summary(bundle)
        assert summary["total_steps"] == 2
        assert summary["approved"] == 2

        worst = get_worst_step(bundle)
        assert worst is not None
        assert worst.get("min_clearance") is not None

        steps = list_critical_steps(bundle)
        assert len(steps) > 0

        artifacts = get_artifact_index(bundle)
        assert isinstance(artifacts, dict)
        assert "episode_summary" in artifacts or "clearance_curve" in artifacts

        # 5. build deterministic diagnostic report
        report_md = build_diagnostic_report(bundle)
        assert episode_dir.name in report_md
        assert "## Safety Summary" in report_md
        assert "## Deterministic Safety Boundary" in report_md
        assert "planner" in report_md

        # 6. run fake diagnostic agent
        agent_result = run_diagnostic_agent(
            context_path=ctx_result.json_path,
            output_dir=tmp_path / "agent_report",
            provider="fake",
        )
        assert agent_result["provider"] == "fake"
        agent_report_path = Path(agent_result["report_path"])
        assert agent_report_path.exists()
        agent_text = agent_report_path.read_text(encoding="utf-8")
        assert episode_dir.name in agent_text
        assert "Boundary Statement" in agent_text

        # 7. verify no DeepSeek API key required
        assert "DEEPSEEK_API_KEY" not in agent_text
