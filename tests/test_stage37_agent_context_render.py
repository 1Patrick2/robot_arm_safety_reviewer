import json
from pathlib import Path

from agent_context.models import AgentContext, AgentContextArtifact, AgentContextStep
from agent_context.render import (
    render_agent_context_json,
    render_agent_context_markdown,
    write_agent_context_files,
)


def _sample_context() -> AgentContext:
    return AgentContext(
        episode_id="ep_001",
        sequence_id="seq_001",
        backend="mock",
        total_steps=3,
        approved_steps=1,
        executed_steps=1,
        blocked_steps=2,
        rejected_steps=1,
        manual_review_steps=1,
        min_clearance=-0.05,
        worst_sequence_step_index=2,
        critical_steps=(
            AgentContextStep(step_index=2, decision="reject", risk_level="high", executed=False, blocked_reason="rejected_by_safety_gate", min_clearance=-0.05),
            AgentContextStep(step_index=3, decision="manual_review", risk_level="medium", executed=False, blocked_reason="manual_review_required", min_clearance=0.01),
        ),
        artifacts=(
            AgentContextArtifact(kind="summary", path="/tmp/ep_001/episode_summary.md", description="summary"),
            AgentContextArtifact(kind="clearance_curve", path="/tmp/ep_001/clearance_curve.png"),
        ),
    )


class TestRenderAgentContextJson:
    def test_renders_dict(self):
        ctx = _sample_context()
        d = render_agent_context_json(ctx)
        assert d["episode_id"] == "ep_001"
        assert d["total_steps"] == 3
        assert len(d["critical_steps"]) == 2
        assert len(d["artifacts"]) == 2


class TestRenderAgentContextMarkdown:
    def test_contains_episode_overview(self):
        ctx = _sample_context()
        md = render_agent_context_markdown(ctx)
        assert "# Diagnostic Context" in md
        assert "Episode ID: ep_001" in md
        assert "Safety Summary" in md
        assert "Total Steps: 3" in md

    def test_contains_critical_steps_table(self):
        ctx = _sample_context()
        md = render_agent_context_markdown(ctx)
        assert "## Critical Steps" in md
        assert "reject" in md
        assert "manual_review" in md

    def test_contains_artifacts(self):
        ctx = _sample_context()
        md = render_agent_context_markdown(ctx)
        assert "## Artifacts" in md
        assert "clearance_curve" in md

    def test_contains_boundary_statement(self):
        ctx = _sample_context()
        md = render_agent_context_markdown(ctx)
        assert "Deterministic Safety Boundary" in md
        assert "No LLM was involved" in md

    def test_contains_limitations(self):
        ctx = _sample_context()
        md = render_agent_context_markdown(ctx)
        assert "## Known Limitations" in md
        for lim in ctx.limitations:
            assert lim in md

    def test_empty_context_still_renders(self):
        ctx = AgentContext(episode_id="ep_empty")
        md = render_agent_context_markdown(ctx)
        assert "ep_empty" in md
        assert "Critical Steps" in md


class TestWriteAgentContextFiles:
    def test_writes_json_and_md(self, tmp_path):
        ctx = _sample_context()
        json_path, md_path = write_agent_context_files(ctx, tmp_path)
        assert json_path.exists()
        assert md_path.exists()

        # Validate JSON content
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["episode_id"] == "ep_001"

        # Validate MD content
        md_text = md_path.read_text(encoding="utf-8")
        assert "# Diagnostic Context" in md_text
