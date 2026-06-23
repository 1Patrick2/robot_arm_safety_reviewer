"""Manual real LLM diagnostic smoke test — requires API key.

Skipped unless ``RUN_REAL_LLM_SMOKE`` is set.
Requires ``LLM_PROVIDER`` (default ``deepseek``) and corresponding API key.
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_REAL_LLM_SMOKE"),
    reason="Set RUN_REAL_LLM_SMOKE=1 with DEEPSEEK_API_KEY or OPENAI_API_KEY",
)


def test_real_llm_diagnostic_analysis():
    """Call the real OpenAI-compatible LLM client with structured evidence."""
    provider = os.environ.get("LLM_PROVIDER", "deepseek")

    if provider == "deepseek":
        if not os.environ.get("DEEPSEEK_API_KEY"):
            pytest.skip("DEEPSEEK_API_KEY not set")
    elif provider in ("openai", "openai-compatible"):
        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
    else:
        pytest.skip(f"Unsupported LLM_PROVIDER: {provider}")

    from diagnostics.analysis.llm_client import call_llm_diagnostic_analysis

    context = {
        "episode_id": "manual_smoke", "total_steps": 2,
        "approved_steps": 0, "rejected_steps": 1, "manual_review_steps": 0,
        "min_clearance": -0.05, "closest_obstacle": "sphere_01",
        "closest_robot_link": "link_3",
    }
    manifest = {
        "evidence_groups": {"geometry": {"available": True}, "safety": {"available": True}},
        "checks": {"has_perception_evidence": False},
    }
    ext_record = {"dataset_name": "manual_smoke", "frame_count": 3, "action_type": "joint_position"}

    answer = call_llm_diagnostic_analysis(
        provider=provider,
        context=context,
        manifest=manifest,
        external_trajectory_record=ext_record,
    )

    assert answer.schema_version == "llm_final_answer.v1"
    assert answer.provider == provider
    assert answer.advisory_decision in {"approve", "manual_review", "reject", "unknown"}
    assert answer.risk_level in {"low", "medium", "high", "unknown"}
    assert any("advisory only" in l for l in answer.limitations)
