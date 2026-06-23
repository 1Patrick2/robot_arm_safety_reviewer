import json
from pathlib import Path

from diagnostics.runtime.models import DiagnosticRuntimeRequest, DiagnosticRuntimeResult
from diagnostics.runtime.runner import run_diagnostic_runtime
from diagnostics.runtime.trace import write_runtime_trace

SAMPLES = Path(__file__).resolve().parents[1] / "bench" / "samples" / "policy_sequences"
BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"


def _sandbox_and_build_context(tmp_path) -> Path:
    """Run sandbox → metrics → context and return the context json path."""
    from application.sandbox_service import SandboxRunRequest, run_sandbox
    from application.agent_context_service import AgentContextBuildRequest, build_agent_context

    db_path = tmp_path / "metrics.db"
    sandbox_result = run_sandbox(
        SandboxRunRequest(
            sequence_path=SAMPLES / "simple_safe_sequence.json",
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            output_root=tmp_path / "sandbox",
            metrics_db=db_path,
        )
    )
    ep_id = sandbox_result.sequence_runtime_result.episode_dir.name
    ctx_result = build_agent_context(
        AgentContextBuildRequest(
            episode_id=ep_id,
            db_path=db_path,
            output_dir=tmp_path / "context",
        )
    )
    return ctx_result.json_path


class TestRuntimeRunner:
    def test_run_without_agent(self, tmp_path):
        ctx_path = _sandbox_and_build_context(tmp_path)
        result = run_diagnostic_runtime(
            DiagnosticRuntimeRequest(
                context_path=ctx_path,
                output_dir=tmp_path / "output",
                run_agent=False,
            )
        )
        assert result.deterministic_report_path.exists()
        report_text = result.deterministic_report_path.read_text(encoding="utf-8")
        assert "## Deterministic Safety Boundary" in report_text
        assert result.agent_report_path is None
        assert result.trace_path.exists()
        trace = json.loads(result.trace_path.read_text(encoding="utf-8"))
        assert trace["schema_version"] == "diagnostic_runtime_trace.v1"

    def test_run_with_fake_agent(self, tmp_path):
        ctx_path = _sandbox_and_build_context(tmp_path)
        result = run_diagnostic_runtime(
            DiagnosticRuntimeRequest(
                context_path=ctx_path,
                output_dir=tmp_path / "output2",
                provider="fake",
                run_agent=True,
            )
        )
        assert result.deterministic_report_path.exists()
        assert result.agent_report_path is not None
        assert result.agent_report_path.exists()
        assert result.trace_path.exists()
        # No violations from fake agent
        assert result.safety_violations == ()

    def test_run_to_dict(self, tmp_path):
        ctx_path = _sandbox_and_build_context(tmp_path)
        result = run_diagnostic_runtime(
            DiagnosticRuntimeRequest(
                context_path=ctx_path,
                output_dir=tmp_path / "output3",
                run_agent=False,
            )
        )
        d = result.to_dict()
        assert "context_path" in d
        assert "deterministic_report_path" in d
        assert "trace_path" in d


class TestRuntimeTrace:
    def test_write_trace(self, tmp_path):
        result = DiagnosticRuntimeResult(
            context_path=tmp_path / "ctx.json",
            deterministic_report_path=tmp_path / "report.md",
            agent_report_path=tmp_path / "agent.md",
            trace_path=tmp_path / "trace.json",
            safety_violations=("approve this action",),
        )
        # Create minimal report file so trace can reference it
        result.deterministic_report_path.write_text("# Report", encoding="utf-8")
        result.agent_report_path.write_text("# Agent", encoding="utf-8")

        trace_path = write_runtime_trace(result)
        assert trace_path.exists()
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        assert trace["has_violations"] is True
        assert "approve this action" in trace["safety_violations"]
