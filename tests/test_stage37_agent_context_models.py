from diagnostic_runtime.context.models import (
    DEFAULT_LIMITATIONS,
    AgentContext,
    AgentContextArtifact,
    AgentContextStep,
)


class TestAgentContextArtifact:
    def test_to_dict(self):
        art = AgentContextArtifact(kind="clearance_curve", path="/tmp/curve.png", description="Clearance curve")
        d = art.to_dict()
        assert d["kind"] == "clearance_curve"
        assert d["path"] == "/tmp/curve.png"
        assert d["description"] == "Clearance curve"

    def test_description_defaults_to_none(self):
        art = AgentContextArtifact(kind="summary", path="/tmp/s.md")
        assert art.description is None


class TestAgentContextStep:
    def test_to_dict(self):
        step = AgentContextStep(
            step_index=1,
            step_id="s1",
            decision="reject",
            risk_level="high",
            executed=False,
            blocked_reason="rejected_by_safety_gate",
            min_clearance=-0.05,
            backend_worst_step=3,
            proposed_action={"target_joints": [0.1, 0.1, 0, 0, 0, 0]},
            safety_result={"decision": "reject", "min_clearance": -0.05},
        )
        d = step.to_dict()
        assert d["step_index"] == 1
        assert d["decision"] == "reject"
        assert d["executed"] is False
        assert d["blocked_reason"] == "rejected_by_safety_gate"
        assert d["min_clearance"] == -0.05
        assert d["proposed_action"]["target_joints"] == [0.1, 0.1, 0, 0, 0, 0]
        assert d["safety_result"]["decision"] == "reject"

    def test_defaults(self):
        step = AgentContextStep()
        d = step.to_dict()
        assert d["step_index"] is None
        assert d["decision"] is None
        assert d["executed"] is False


class TestAgentContext:
    def test_to_dict(self):
        ctx = AgentContext(
            episode_id="ep_001",
            sequence_id="seq_001",
            backend="mock",
            total_steps=2,
            approved_steps=1,
            rejected_steps=1,
            blocked_steps=1,
            executed_steps=0,
            min_clearance=0.01,
            worst_sequence_step_index=1,
            critical_steps=(
                AgentContextStep(step_index=1, decision="reject", executed=False),
            ),
            artifacts=(
                AgentContextArtifact(kind="summary", path="/tmp/s.md"),
            ),
        )
        d = ctx.to_dict()
        assert d["episode_id"] == "ep_001"
        assert d["total_steps"] == 2
        assert len(d["critical_steps"]) == 1
        assert len(d["artifacts"]) == 1
        assert d["critical_steps"][0]["decision"] == "reject"

    def test_default_limitations(self):
        ctx = AgentContext(episode_id="ep_001")
        assert len(ctx.limitations) == len(DEFAULT_LIMITATIONS)
        assert any("deterministic safety reviewer" in text for text in ctx.limitations)

    def test_limitations_are_immutable(self):
        ctx = AgentContext(episode_id="ep_001")
        d = ctx.to_dict()
        assert isinstance(d["limitations"], list)

    def test_empty_critical_steps(self):
        ctx = AgentContext(episode_id="ep_002")
        d = ctx.to_dict()
        assert d["critical_steps"] == []
        assert d["artifacts"] == []

    def test_list_inputs_normalised_to_tuple(self, tmp_path):
        ctx = AgentContext(
            episode_id="ep_003",
            critical_steps=[
                AgentContextStep(step_index=1, decision="reject"),
            ],
            artifacts=[
                AgentContextArtifact(kind="summary", path="/tmp/s.md"),
            ],
            limitations=["custom limitation"],
        )
        assert isinstance(ctx.critical_steps, tuple)
        assert isinstance(ctx.artifacts, tuple)
        assert isinstance(ctx.limitations, tuple)
        d = ctx.to_dict()
        assert len(d["critical_steps"]) == 1
        assert d["critical_steps"][0]["decision"] == "reject"
